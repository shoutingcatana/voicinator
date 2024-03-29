{
  inputs = {
    dream2nix.url = "github:nix-community/dream2nix";
    nixpkgs.follows = "dream2nix/nixpkgs";
  };

  outputs =
    { self, dream2nix, nixpkgs, }:
    let
      system = "x86_64-linux";
      lib = nixpkgs.lib;
      pkgs = nixpkgs.legacyPackages.${system};
      packageModule =
        { dream2nix, config, ... }:
        {
          imports = [ dream2nix.modules.dream2nix.WIP-python-pdm ];
          pdm.lockfile = ./pdm.lock;
          pdm.pyproject = ./pyproject.toml;
          paths.package = ./.;
          paths.projectRoot = ./.;
          paths.projectRootFile = "flake.nix";
          overrides = {
            gpt-engineer = {
              mkDerivation.buildInputs = [ config.deps.python.pkgs.poetry-core ];
              mkDerivation.propagatedBuildInputs = [ config.deps.python.pkgs.tkinter ];
            };
          };
        };
      package = dream2nix.lib.evalModules {
        modules = [ packageModule ];
        packageSets.nixpkgs = pkgs;
      };
    in
    {
      packages.${system}.default = package;
      devShells.${system}.default = pkgs.mkShell {
        inputsFrom = [ package.devShell ];
        packages = [
          pkgs.pdm
          pkgs.imagemagickBig
        ];
        buildInputs = [ pkgs.portaudio ];
        shellHook = ''
          if [ -e .env ]; then
            source .env
          fi
          echo "$(which python)" > .pdm-python
          export PYTHONPATH="$PYTHONPATH:$(realpath ../clan-cli)"
          export LD_LIBRARY_PATH="${pkgs.portaudio}/lib:${lib.getLib pkgs.libsndfile}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        '';
      };
    };
}
