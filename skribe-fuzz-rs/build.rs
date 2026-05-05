use std::env;
use std::process::Command;

fn main() {
    let out_dir = env::var("OUT_DIR").unwrap();
    let kdist_path = format!("{}/kdist", out_dir);

    let _output = Command::new("kdist")
        .env("KDIST_DIR", &kdist_path)
        .arg("-v")
        .arg("build")
        .arg("stylus-semantics.llvm-library")
        .output()
        .expect("Failed to build the kllvm library with kdist");

    let llvm_library_path = format!("{}/stylus-semantics/llvm-library", kdist_path);

    println!("cargo:rustc-link-search={}", llvm_library_path);

    println!("cargo:rustc-link-lib=dylib:+verbatim=interpreter.so");
}

