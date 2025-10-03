{
  description = "skribe - Property testing for Stylus smart contracts";
  inputs = {
    rv-nix-tools.url = "github:runtimeverification/rv-nix-tools/854d4f05ea78547d46e807b414faad64cea10ae4";
    nixpkgs.follows = "rv-nix-tools/nixpkgs";
  
    flake-utils.url = "github:numtide/flake-utils";
    k-framework.url = "github:runtimeverification/k/v7.1.276";
    k-framework.inputs.nixpkgs.follows = "nixpkgs";
    uv2nix.url = "github:pyproject-nix/uv2nix/be511633027f67beee87ab499f7b16d0a2f7eceb";
    # uv2nix requires a newer version of nixpkgs
    # therefore, we pin uv2nix specifically to a newer version of nixpkgs
    # until we replaced our stale version of nixpkgs with an upstream one as well
    # but also uv2nix requires us to call it with `callPackage`, so we add stuff
    # from the newer nixpkgs to our stale nixpkgs via an overlay
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    uv2nix.inputs.nixpkgs.follows = "nixpkgs-unstable";
    # uv2nix.inputs.nixpkgs.follows = "nixpkgs";
    pyproject-build-systems.url = "github:pyproject-nix/build-system-pkgs/dbfc0483b5952c6b86e36f8b3afeb9dde30ea4b5";
    pyproject-build-systems = {
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.uv2nix.follows = "uv2nix";
      inputs.pyproject-nix.follows = "uv2nix/pyproject-nix";
    };
    pyproject-nix.follows = "uv2nix/pyproject-nix";

    rust-overlay.url = "github:oxalica/rust-overlay";
  };
  outputs = { self, rv-nix-tools, nixpkgs, flake-utils, pyproject-nix, pyproject-build-systems, uv2nix, k-framework, rust-overlay, nixpkgs-unstable }:
  let
    pythonVer = "310";
  in flake-utils.lib.eachSystem [
      "x86_64-linux"
      "x86_64-darwin"
      "aarch64-linux"
      "aarch64-darwin"
    ] (system:
    let
      pkgs-unstable = import nixpkgs-unstable {
        inherit system;
      };
      # for uv2nix, remove this once we updated to a newer version of nixpkgs
      staleNixpkgsOverlay = final: prev: {
        inherit (pkgs-unstable) replaceVars;
      };
      # due to the nixpkgs that we use in this flake being outdated, uv is also heavily outdated
      # we can instead use the binary release of uv provided by uv2nix for now
      uvOverlay = final: prev: {
        uv = uv2nix.packages.${final.system}.uv-bin;
      };
      # create custom overlay for k, because the overlay in k-framework currently also includes a lot of other stuff instead of only k
      kOverlay = final: prev: {
        k = k-framework.packages.${final.system}.k;
      };
      skribeOverlay = final: prev:
      let
        skribe-pyk = final.callPackage ./nix/skribe-pyk {
          inherit pyproject-nix pyproject-build-systems uv2nix;
          python = final."python${pythonVer}";
        };
        skribe = final.callPackage ./nix/skribe {
          inherit skribe-pyk;
          rev = self.rev or null;
        };
      in {
        inherit skribe;
      };
      pkgs = import nixpkgs {
        inherit system;
        overlays = [
          staleNixpkgsOverlay
          uvOverlay
          kOverlay
          skribeOverlay
          (import rust-overlay)
        ];
      };
      python = pkgs."python${pythonVer}";
    in {
      devShells.default = pkgs.mkShell {
        name = "uv develop shell";
        buildInputs = [
          python
          pkgs.uv
        ];
        env = {
          # prevent uv from managing Python downloads and force use of specific 
          UV_PYTHON_DOWNLOADS = "never";
          UV_PYTHON = python.interpreter;
        };
        shellHook = ''
          unset PYTHONPATH
        '';
      };
      packages = rec {
        inherit (pkgs) skribe;
        default = skribe;
      };
    }) // {
      overlays.default = final: prev: {
        inherit (self.packages.${final.system}) skribe;
      };
    };
}
