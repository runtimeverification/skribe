{
  lib,
  stdenv,
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

  skribe-pyk,
  rev ? null
}:
stdenv.mkDerivation {
  pname = "skribe-kdist";
  version = if (rev != null) then rev else "dirty";

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

  src = callPackage ../skribe-source { };

  dontUseCmakeConfigure = true;

  enableParallelBuilding = true;

  buildPhase = ''
    XDG_CACHE_HOME=$(pwd) ${
      lib.optionalString
      (stdenv.isAarch64 && stdenv.isDarwin)
      "APPLE_SILICON=true"
    } _JAVA_OPTIONS="-Xmx32g" skribe-kdist -v build 'stylus-semantics.*'
  '';

  installPhase = ''
    mkdir -p $out/kdist
    cp -r ./kdist-*/* $out/kdist/
  '';
}
