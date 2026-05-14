use std::env;

fn main() {
    let llvm_library_path = env::var("KLLVM_LIBRARY_PATH").expect(
        "KLLVM_LIBRARY_PATH must be set to the directory containing the interpeter shared object",
    );
    println!(
        "cargo:rustc-link-arg={}/interpreter.{}",
        llvm_library_path,
        std::env::consts::DLL_EXTENSION
    );
}
