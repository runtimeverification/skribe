#![no_main]
use std::{cell::Cell, sync::OnceLock};

use libfuzzer_sys::fuzz_target;

use pico_args::Arguments;

use skribe_fuzz_rs::{
    Signature, fuzz_specs_from_json,
    kllvm::{self, MarshalError, Marshaller, VarHandler},
    kore,
};

struct FuzzConfig {
    template: kore::Pattern,
    signatures: Vec<Signature>,
    contract_name: String,
    function_name: String,
}

// TODO: Implement ABI parsing and Arbitrary value generation
struct SignatureFuzzer;

impl VarHandler for SignatureFuzzer {
    fn substitute(
        &mut self,
        name: &str,
        _sort: &kore::Sort,
    ) -> Result<kore::Pattern, kllvm::MarshalError> {
        let sort = kore::Sort::App {
            id: kore::Id::new("SortBytes".to_string()).unwrap(),
            args: vec![],
        };
        match name {
            "VarCALLDATA" => Ok(kore::Pattern::Dv {
                sort,
                // TODO: Implement ABI encoding
                value: "00".into(),
            }),
            _ => Err(MarshalError::Unsupported(
                "Encountered a variable that isn't CALLDATA",
            )),
        }
    }
}

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
    let mut specs = fuzz_specs_from_json(&contents).unwrap();
    let spec = specs.remove(0); // Assuming only one spec came from the json
    let mut parser = kore::Parser::new(&spec.template).unwrap();
    let template = parser.pattern().unwrap();

    FUZZ_CONFIG.replace(Some(FuzzConfig { template, signatures: spec.signatures, contract_name, function_name }));
},
    |data: &[u8]| {
        let mut marshaller_cell: Option<Marshaller<_>> = MARSHALLER.take();
        let marshaller = marshaller_cell.as_mut().unwrap();
        let config_cell = FUZZ_CONFIG.take();
        let config = config_cell.as_ref().unwrap();

        // Marshal over to kllvm with the CALLDATA variable substituted
        let sig = SignatureFuzzer{};
        marshaller.set_handler(sig);
        let template = &config.template;
        let kllvm_pattern: kllvm::Pattern = marshaller.marshal(template).unwrap();

        // Execute the semantics
        let mut block: kllvm::Block = kllvm_pattern.into();
        block.take_steps(-1);

        // Check the exit code
        let exit_code = get_exit_code(&block);
        if exit_code != 0 {
            println!("panic!");
        }

        FUZZ_CONFIG.replace(config_cell);
        MARSHALLER.replace(marshaller_cell);
});

fn get_exit_code(block: &kllvm::Block) -> u32 {
    let res_str = format!("{}", block);
    let pattern = r#"Lbl'-LT-'exit-code'-GT-'{}(\dv{SortInt{}}(""#;
    let idx = res_str.find(pattern).unwrap();
    let slice = &res_str[idx + pattern.len()..];
    let idx2 = slice.find(r#"""#).unwrap();
    let num_str = &slice[..idx2];

    num_str.parse().unwrap()
}
