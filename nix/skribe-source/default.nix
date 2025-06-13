{
  lib,
  nix-gitignore
}:

lib.cleanSource (nix-gitignore.gitignoreSourcePure [
    ../../.gitignore
    ".github/"
    "result*"
    "/deps/"
    # do not include submodule directories that might be initilized empty or non-existent
    "/src/tests/integration/data/contracts/stylus-hello-world"
  ] ../../.
)