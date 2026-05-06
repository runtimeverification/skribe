use std::env;

fn main() {
    let llvm_library_path = env::var("KLLVM_LIBRARY_PATH")
        .expect("KLLVM_LIBRARY_PATH must be set to the directory containing interpreter.so");
    println!("cargo:rustc-link-search={}", llvm_library_path);
    println!("cargo:rustc-link-lib=dylib:+verbatim=interpreter.so");
}
