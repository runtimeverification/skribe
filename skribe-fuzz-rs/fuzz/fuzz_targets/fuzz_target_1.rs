#![no_main]
use std::cell::Cell;

use arbitrary::Unstructured;
use libfuzzer_sys::fuzz_target;

use pico_args::Arguments;

use skribe_fuzz_rs::{
    FuzzConfig, SignatureAbi, SignatureFuzzer, extract_template_and_signature,
    fuzz_specs_from_json, get_exit_code,
    kllvm::{self, Marshaller},
    kore,
};

// Persistent data across iterations.
//
// FUZZ_CONFIG - The fuzz spec + contract/function names to fuzz. Parsed from the command line
// MARSHALLER  - The marshaller for moving terms over to kllvm. Keeps parts of the template
//               configuration cached.
thread_local! {
    static FUZZ_CONFIG: Cell<Option<FuzzConfig>> = Cell::new(None);
    static MARSHALLER: Cell<Option<Marshaller<SignatureFuzzer>>> = Cell::new(Some(Marshaller::new(None)))
}

fuzz_target!( init: {
    kllvm::init();

    // Parse arguments
    //
    // You must pass these options as `--xxx=<val>` with the equals sign,
    // otherwise libfuzzer treats `<val>` as a positional argument.
    let mut args = Arguments::from_env();
    let fuzz_spec_file: String = args
        .value_from_str("--fuzz-spec")
        .unwrap();
    let contract_name: String = args
        .value_from_str("--contract-name")
        .unwrap();
    let function_name: String = args
        .value_from_str("--function-name")
        .unwrap();

    // Parse fuzz spec
    let contents = std::fs::read_to_string(fuzz_spec_file).unwrap();
    let specs = fuzz_specs_from_json(&contents).unwrap();
    let (template_str, signature) = extract_template_and_signature(specs, &contract_name, &function_name).unwrap();

    let mut parser = kore::Parser::new(&template_str).unwrap();
    let template = parser.pattern().unwrap();

    let abi = SignatureAbi::from_signature(signature).unwrap();

    FUZZ_CONFIG.replace(Some(FuzzConfig { template, abi }));
},
    |data: &[u8]| {
        let mut marshaller_cell: Option<Marshaller<_>> = MARSHALLER.take();
        let marshaller = marshaller_cell.as_mut().unwrap();
        let config_cell = FUZZ_CONFIG.take();
        let config = config_cell.as_ref().unwrap();

        // Marshal over to kllvm with the CALLDATA variable substituted
        let mut u = Unstructured::new(data);
        let input = config.abi.arbitrary_input(&mut u).unwrap();
        let sig = SignatureFuzzer(input);
        marshaller.set_handler(sig);
        let template = &config.template;
        let kllvm_pattern: kllvm::Pattern = marshaller.marshal(template).unwrap();

        // Execute the semantics
        let mut block: kllvm::Block = kllvm_pattern.into();
        block.take_steps(-1);

        let kore_text = block.to_string();
        let mut parser = kore::Parser::new(&kore_text).unwrap();
        let pattern = parser.pattern().unwrap();

        // Check the exit code
        let exit_code = get_exit_code(&pattern);
        if exit_code != 0 {
            println!("panic!");
        }

        FUZZ_CONFIG.replace(config_cell);
        MARSHALLER.replace(marshaller_cell);
});
