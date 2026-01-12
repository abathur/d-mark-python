{
  inputs = {
    nixpkgs = {
      url = "github:nixos/nixpkgs/nixpkgs-unstable";
      # follows = "comity/nixpkgs";
    };
    flake-utils = {
      url = "github:numtide/flake-utils";
      # follows = "comity/flake-utils";
    };
    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
      # follows = "comity/flake-compat";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  description = "Python port of the D★Mark (semantic) markup language";

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      flake-compat,
      treefmt-nix,
    }:
    {
      overlays.default = final: prev: {
        d-mark-python = final.python3Packages.callPackage ./d-mark-python.nix {
          # TODO: this won't work since it isn't in nixpkgs atm
          # version = prev.d-mark-python.version + "-" + (self.shortRev or "dirty");
          version = "unstable" + "-" + (self.shortRev or "dirty");
          src = final.lib.cleanSource self;
        };
      };
    }
    // flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            self.overlays.default
          ];
        };

        treefmtEval = (treefmt-nix.lib.evalModule pkgs ./treefmt.nix);

      in
      {
        packages = {
          inherit (pkgs) d-mark-python;
          default = pkgs.d-mark-python;
        };
        checks = {
          formatting = treefmtEval.config.build.check self;
        };
        formatter = treefmtEval.config.build.wrapper;
        devShells = {
          default = pkgs.mkShell {
            PYTHONDONTWRITEBYTECODE = 1;
            inputsFrom = [ pkgs.d-mark-python ];
            packages = [ ];
          };
          idk = pkgs.mkShell {
            buildInputs = [ pkgs.d-mark-python ];
          };
        };

      }
    );
}
