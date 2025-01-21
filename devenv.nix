{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/basics/

  # https://devenv.sh/packages/
  packages = with pkgs; [ 
    git 
    python312Packages.mkdocs
    python312Packages.mkdocs-material
    python312Packages.mkdocs-autorefs
    python312Packages.mkdocstrings
    python312Packages.mkdocstrings
  ];

  # https://devenv.sh/scripts/
  scripts.build.exec = ''
    mkdocs build
  '';
  scripts.serve.exec = ''
    mkdocs serve -w docs
  '';

  enterShell = ''
    echo "Run 'build' to run the build script"
  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/pre-commit-hooks/
  pre-commit.hooks.check-yaml.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
