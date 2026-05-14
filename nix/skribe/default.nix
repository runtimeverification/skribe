{
  lib,
  stdenv,
  makeWrapper,
  callPackage,

  k,
  which,
  rust-bin,

  skribe-rust ? null,
  skribe-pyk,
  skribe-kdist,
  skribe-fuzz,
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

  dontUnpack = true;

  nativeBuildInputs = [ makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin

    makeWrapper ${skribe-pyk}/bin/skribe-simulation $out/bin/skribe-simulation --prefix PATH : ${
      lib.makeBinPath
      ([ which k skribe-fuzz ] ++ lib.optionals (skribe-rust != null) [
        skribe-rust
      ])
    } --set KDIST_DIR ${skribe-kdist}/kdist

    makeWrapper ${skribe-pyk}/bin/skribe $out/bin/skribe --prefix PATH : ${
      lib.makeBinPath
      ([ which k skribe-fuzz ] ++ lib.optionals (skribe-rust != null) [
        skribe-rust
      ])
    } --set KDIST_DIR ${skribe-kdist}/kdist
  '';

  passthru = if skribe-rust == null then {
    rust = callPackage ./default.nix (args // { skribe-rust = rustWithWasmTarget; });
  } else { };
}
