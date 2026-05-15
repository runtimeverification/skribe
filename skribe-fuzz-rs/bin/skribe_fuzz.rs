use arbitrary::Unstructured;
use pico_args::Arguments;
use skribe_fuzz_rs::{
    FuzzConfig, SignatureAbi, SignatureFuzzer, extract_template_and_signature,
    fuzz_specs_from_json, get_coverage_size, get_exit_code,
    kllvm::{self, Marshaller},
    kore, write_coverage_data,
};

use std::cell::Cell;
use std::path::PathBuf;
use std::ptr;

use libafl::{
    Fuzzer, StdFuzzer,
    corpus::{InMemoryCorpus, OnDiskCorpus},
    events::SimpleEventManager,
    executors::{ExitKind, InProcessExecutor},
    feedbacks::{CrashFeedback, MaxMapFeedback},
    generators::RandPrintablesGenerator,
    inputs::BytesInput,
    monitors::SimpleMonitor,
    mutators::{HavocScheduledMutator, havoc_mutations},
    nonzero,
    observers::StdMapObserver,
    schedulers::QueueScheduler,
    stages::StdMutationalStage,
    state::StdState,
};
use libafl_bolts::{rands::StdRand, tuples::tuple_list};

// Byte array pointer/size for the coverage updates
// Initialized on startup
static mut SIGNALS_PTR: *mut u8 = ptr::null_mut();
static mut SIGNALS_LEN: usize = 0;

// Persistent data across iterations.
//
// FUZZ_CONFIG - The fuzz spec + contract/function names to fuzz. Parsed from the command line
// MARSHALLER  - The marshaller for moving terms over to kllvm. Keeps parts of the template
//               configuration cached.
thread_local! {
    static FUZZ_CONFIG: Cell<Option<FuzzConfig>> = const { Cell::new(None) };
    static MARSHALLER: Cell<Option<Marshaller<SignatureFuzzer>>> = Cell::new(Some(Marshaller::new(None)))
}

fn main() {
    kllvm::init();

    // Parse Arguments
    let mut args = Arguments::from_env();
    let fuzz_spec_file: String = args.value_from_str("--fuzz-spec").unwrap();
    let contract_name: String = args.value_from_str("--contract-name").unwrap();
    let function_name: String = args.value_from_str("--function-name").unwrap();
    let workspace: String = args
        .value_from_str("--workspace")
        .unwrap_or("./workspace".to_string());
    let mut artifacts_path = PathBuf::from(workspace);
    artifacts_path.push(&contract_name);
    artifacts_path.push(&function_name);
    artifacts_path.push("artifacts");

    // Parse fuzz spec
    let contents = std::fs::read_to_string(fuzz_spec_file).unwrap();
    let specs = fuzz_specs_from_json(&contents).unwrap();
    let (template_str, signature) =
        extract_template_and_signature(specs, &contract_name, &function_name).unwrap();

    let mut parser = kore::Parser::new(&template_str).unwrap();
    let template = parser.pattern().unwrap();

    let abi = SignatureAbi::from_signature(signature).unwrap();

    let coverage_size = get_coverage_size(&template);

    FUZZ_CONFIG.replace(Some(FuzzConfig { template, abi }));

    // Create an observation channel for coverage
    let alloc = vec![0u8; coverage_size].into_boxed_slice();
    let leaked: &'static mut [u8] = Box::leak(alloc);
    unsafe {
        SIGNALS_PTR = leaked.as_mut_ptr();
        SIGNALS_LEN = leaked.len();
    }
    let observer = unsafe { StdMapObserver::from_mut_ptr("signals", SIGNALS_PTR, SIGNALS_LEN) };

    // Feedback that rates what's interesting from the observer
    let mut feedback = MaxMapFeedback::new(&observer);

    // Feedback that rates what's a "solution" (test failure)
    let mut objective = CrashFeedback::new();

    // The State holds data that evolves over fuzzing, like the RNG state,
    // the corpus, and metadata.
    let mut state = StdState::new(
        // RNG
        StdRand::new(),
        // Corpus that will save interesting test cases. In memory for now
        // TODO: Save to disk once coverage updates are working.
        InMemoryCorpus::<BytesInput>::new(),
        // Corpus folder in which we store solutions (test failures for us)
        OnDiskCorpus::new(artifacts_path).unwrap(),
        &mut feedback,
        &mut objective,
    )
    .unwrap();

    // The Monitor trait defines how the fuzzer stats are displayed to the user
    let mon = SimpleMonitor::new(|s| println!("{s}"));

    // The event manager handles the various events generated during the fuzzing loop
    // such as the notification of the addition of a new item to the corpus
    let mut mgr = SimpleEventManager::new(mon);

    // A queue policy to get testcases from the corpus
    let scheduler = QueueScheduler::new();

    // A fuzzer with feedbacks and a corpus scheduler
    let mut fuzzer = StdFuzzer::new(scheduler, feedback, objective);

    // The executor which runs the harness
    let mut harness_binding = harness;
    let mut executor = InProcessExecutor::new(
        &mut harness_binding,
        tuple_list!(observer),
        &mut fuzzer,
        &mut state,
        &mut mgr,
    )
    .expect("Failed to create the Executor");

    // The random bytes generator. Generates bytearrays up to length 1024
    let mut generator = RandPrintablesGenerator::new(nonzero!(1024));

    // Generate initial inputs
    state
        .generate_initial_inputs(&mut fuzzer, &mut executor, &mut generator, &mut mgr, 100)
        .expect("Failed to generate the initial corpus");

    // Setup a mutational stage with a basic bytes mutator
    let mutator = HavocScheduledMutator::new(havoc_mutations());
    let mut stages = tuple_list!(StdMutationalStage::new(mutator));

    fuzzer
        .fuzz_loop(&mut stages, &mut executor, &mut state, &mut mgr)
        .expect("Error in the fuzzing loop");
}

fn harness(data: &BytesInput) -> ExitKind {
    let mut marshaller_cell: Option<Marshaller<_>> = MARSHALLER.take();
    let marshaller = marshaller_cell.as_mut().unwrap();
    let config_cell = FUZZ_CONFIG.take();
    let config = config_cell.as_ref().unwrap();

    // Marshal over to kllvm with the CALLDATA variable substituted
    let mut u = Unstructured::new(data.as_ref());
    let input = config.abi.arbitrary_input(&mut u).unwrap();
    let sig = SignatureFuzzer(input);
    marshaller.set_handler(sig);
    let template = &config.template;
    let kllvm_pattern: kllvm::Pattern = marshaller.marshal(template).unwrap();

    // Execute the semantics
    let mut block: kllvm::Block = kllvm_pattern.into();
    block.take_steps(-1);

    FUZZ_CONFIG.replace(config_cell);
    MARSHALLER.replace(marshaller_cell);

    // Record coverage for this run
    let signals: &mut [u8] = unsafe { std::slice::from_raw_parts_mut(SIGNALS_PTR, SIGNALS_LEN) };
    write_coverage_data(&block, signals);

    // Check the exit code
    let exit_code = get_exit_code(&block);
    if exit_code != 0 {
        ExitKind::Crash
    } else {
        ExitKind::Ok
    }
}
