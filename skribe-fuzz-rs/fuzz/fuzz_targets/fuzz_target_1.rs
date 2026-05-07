#![no_main]

use libfuzzer_sys::fuzz_target;

use pico_args::Arguments;

use skribe_fuzz_rs::{kllvm, fuzz_specs_from_json, make_dv};

fuzz_target!( init: {
    kllvm::init();
    let mut args = Arguments::from_env();

    let fuzz_spec_file: Option<String> = args
        // You must pass this option as `--fuzz-spec=<specfile>` with the
        // equals sign, otherwise libfuzzer treats it as a positional argument
        .opt_value_from_str("--fuzz-spec")
        .unwrap();

    if let Some(file) = fuzz_spec_file {
        let contents = std::fs::read_to_string(file).unwrap();
        let specs = fuzz_specs_from_json(&contents).unwrap();
        println!("{:?}", specs);
    }
},
    |data: &[u8]| {
    let _ = make_dv();
    // fuzzed code goes here
});
