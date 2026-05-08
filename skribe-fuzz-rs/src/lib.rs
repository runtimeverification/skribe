mod abi;
mod fuzz_spec;

pub use abi::SignatureAbi;
pub use fuzz_spec::{FuzzSpec, Signature, fuzz_specs_from_json};

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
