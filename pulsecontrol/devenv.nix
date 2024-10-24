{ pkgs, lib, config, inputs, ... }:
let
    pkgs-unstable = import inputs.nixpkgs-unstable { system = pkgs.stdenv.system; };
in
{
  # https://devenv.sh/basics/
  dotenv.enable = true;
  env.GREET = "Python+Rye";
  env.RYE_TOOLCHAIN = "cpython${pkgs.python3.version}";
  env.RYE_TOOLCHAIN_VERSION = "${pkgs.python3.version}";
  env.LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";

  # https://devenv.sh/packages/
  packages = with pkgs; [
      git
      libcap
      libz
      libcamera
      libGL
      opencv2
  ];

  # https://devenv.sh/languages/
  languages.python = {
     enable = true;
     package = pkgs.python3;
     uv.enable = true;
     uv.sync.enable = true;
     uv.sync.allExtras = true;
     uv.package = pkgs-unstable.uv;
  };

  # https://devenv.sh/processes/
  # processes.cargo-watch.exec = "cargo-watch";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts.hello.exec = ''
    echo $GREET
  '';

  enterShell = ''
    echo $GREET
  '';

  # https://devenv.sh/tasks/
  tasks = {
    "pulsecontrol:start" = {
      exec = "uv run ";
    };
  };
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
    git --version | grep --color=auto "${pkgs.git.version}"
    rye run pytest
  '';

  # https://devenv.sh/pre-commit-hooks/
  # pre-commit.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
