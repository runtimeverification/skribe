use skribe_fuzz_rs::{SignatureAbi, kore, extract_template_and_signature, fuzz_specs_from_json};
use pico_args::Arguments;

fn main() {
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
}
