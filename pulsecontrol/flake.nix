{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      fhs = pkgs.buildFHSUserEnv {
        name = "fhs-shell";
        targetPkgs = pkgs: (with pkgs; 
        [
          gcc 
          libtool 
          rye 
          ruff
          libz
          libcamera
          libGL
          glib
          opencv2
        ] );
      };
    in
      {
        devShells.${system}.default = fhs.env;
      };
}
