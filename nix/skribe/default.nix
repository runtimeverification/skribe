{
  lib,
  stdenv,
  makeWrapper,
  callPackage,

  k,
  which,

  skribe-pyk,
  rev ? null
} @ args:

stdenv.mkDerivation {
  pname = "skribe";
  version = if (rev != null) then rev else "dirty";
  buildInputs = [
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
    mkdir -p $out
    cp -r ./kdist-*/* $out/
    mkdir -p $out/bin
    makeWrapper ${skribe-pyk}/bin/skribe-simulation $out/bin/skribe-simulation --prefix PATH : ${lib.makeBinPath [ which k ]} --set KDIST_DIR $out
  '';
}