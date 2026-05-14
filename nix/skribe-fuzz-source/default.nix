{
  lib,
  nix-gitignore
}:

lib.cleanSource (nix-gitignore.gitignoreSourcePure [
    ../../.gitignore
    "result*"
    "target/"
  ] ../../skribe-fuzz-rs
)
