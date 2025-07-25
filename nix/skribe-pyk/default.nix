{
  lib,
  callPackage,
  nix-gitignore,

  pyproject-nix,
  pyproject-build-systems,
  uv2nix,

  python
}:
let
  pyproject-util = callPackage pyproject-nix.build.util {};
  pyproject-packages = callPackage pyproject-nix.build.packages {
    inherit python;
  };

  # load a uv workspace from a workspace root
  workspace = uv2nix.lib.workspace.loadWorkspace {
    workspaceRoot = callPackage ../skribe-source { };
  };

  # create overlay
  lockFileOverlay = workspace.mkPyprojectOverlay {
    # prefer "wheel" over "sdist" due to maintance overhead
    # there is no bundled set of overlays for "sdist" in uv2nix, in contrast to poetry2nix
    sourcePreference = "wheel";
  };

  buildSystemsOverlay = import ./build-systems-overlay.nix;

  # construct package set
  pythonSet = pyproject-packages.overrideScope (lib.composeManyExtensions [
    # make build tools available by default as these are not necessarily specified in python lock files
    pyproject-build-systems.overlays.default
    # include all packages from the python lock file
    lockFileOverlay
    # add build system overrides to certain python packages
    buildSystemsOverlay
  ]);
in pyproject-util.mkApplication {
  # default dependancy group enables no optional dependencies and no dependency-groups
  venv = pythonSet.mkVirtualEnv "skribe-env" workspace.deps.default;
  package = pythonSet.skribe;
}
