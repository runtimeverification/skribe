{
  lib,
  stdenv,
  makeWrapper,
  callPackage,

  clang,
  cmake,
  git,
  k,
  boost,
  mpfr,
  openssl,
  gmp,
  secp256k1,
  which,
  rust-bin,

  skribe-rust ? null,
  skribe-pyk,
  rev ? null
} @ args:
let
  rustWithWasmTarget = rust-bin.stable.latest.default.override {
    targets = [ "wasm32-unknown-unknown" ];
  };
in
stdenv.mkDerivation {
  pname = "skribe";
  version = if (rev != null) then rev else "dirty";

  outputs = [
    "bin"
    # contains kdist artifacts
    "out"
    # this empty `dev` output is required as we otherwise get cyclic dependencies between `bin` and `out`
    # this is due to a setup-hook creating references in a new directory `nix-support` in either `out` or `dev`
    "dev"
  ];

  buildInputs = [
    clang
    cmake
    git
    boost
    mpfr
    openssl
    gmp
    secp256k1
    skribe-pyk
    k
  ];

  nativeBuildInputs = [ makeWrapper ];

  src = callPackage ../skribe-source { };

  dontUseCmakeConfigure = true;

  enableParallelBuilding = true;

  buildPhase = ''
    XDG_CACHE_HOME=$(pwd) ${
      lib.optionalString
      (stdenv.isAarch64 && stdenv.isDarwin)
      "APPLE_SILICON=true"
    } skribe-kdist -v build 'stylus-semantics.*'
  '';

  installPhase = ''
    mkdir -p $bin/bin
    mkdir -p $out/kdist

    cp -r ./kdist-*/* $out/kdist/

    makeWrapper ${skribe-pyk}/bin/skribe-simulation $bin/bin/skribe-simulation --prefix PATH : ${
      lib.makeBinPath
      ([ which k ] ++ lib.optionals (skribe-rust != null) [
        skribe-rust
      ])
    } --set KDIST_DIR $out/kdist

    makeWrapper ${skribe-pyk}/bin/skribe $bin/bin/skribe --prefix PATH : ${
      lib.makeBinPath
      ([ which k ] ++ lib.optionals (skribe-rust != null) [
        skribe-rust
      ])
    } --set KDIST_DIR $out/kdist
  '';

  passthru = if skribe-rust == null then {
    # list all supported solc versions here
    rust = callPackage ./default.nix (args // { skribe-rust = rustWithWasmTarget; });
  } else { };
}