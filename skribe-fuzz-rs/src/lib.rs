mod abi;
mod fuzz_config;
mod fuzz_spec;

pub use abi::SignatureAbi;
pub use fuzz_config::{FuzzConfig, SignatureFuzzer};
pub use fuzz_spec::{FuzzSpec, Signature, extract_template_and_signature, fuzz_specs_from_json};

pub use kframework::kore;
pub use kframework_ffi::kllvm;

/// Get the <exit-code> cell value from a configuration
pub fn get_exit_code(block: &kllvm::Block) -> u32 {
    let res_str = format!("{}", block);
    let pattern = r#"Lbl'-LT-'exit-code'-GT-'{}(\dv{SortInt{}}(""#;
    let idx = res_str.find(pattern).unwrap();
    let slice = &res_str[idx + pattern.len()..];
    let idx2 = slice.find(r#"""#).unwrap();
    let num_str = &slice[..idx2];

    num_str.parse().unwrap()
}

pub fn write_coverage_data(block: &kllvm::Block, coverage: &mut [u8]) {
    // Update coverage
    // This should come in as a zeroed byte array every time, as it gets reset
    // by the observer at the beginning of each execution
}

pub fn get_coverage_size(config: &kore::Pattern) -> usize {
    100
}
