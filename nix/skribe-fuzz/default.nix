{
  lib,
  callPackage,
  makeRustPlatform,
  rust-bin,

  skribe-kdist,
  rev ? null
}:
let
  rustToolchain = rust-bin.fromRustupToolchainFile ../rust-toolchain.toml;
  rustPlatform = makeRustPlatform {
    cargo = rustToolchain;
    rustc = rustToolchain;
  };
  cargoToml = lib.importTOML ../../skribe-fuzz-rs/Cargo.toml;
in
rustPlatform.buildRustPackage {
  pname = "skribe-fuzz";
  version = if (rev != null) then rev else cargoToml.workspace.package.version;

  src = callPackage ../skribe-fuzz-source { };

  cargoLock = {
    lockFile = ../../skribe-fuzz-rs/Cargo.lock;
    outputHashes = {
      "kframework-0.1.0" = "sha256-6O13hRZ/jGyHjildOnN3yaYxM5hFfor9ooX4pP1MW3A=";
    };
  };

  nativeBuildInputs = [ rustPlatform.bindgenHook ];

  KLLVM_LIBRARY_PATH = "${skribe-kdist}/kdist/stylus-semantics/llvm-library";

  # cargo-auditable in nixpkgs predates edition 2024 support
  auditable = false;

  doCheck = false;

  meta = {
    description = "libafl-based fuzzer for skribe";
    mainProgram = "skribe-fuzz";
  };
}
