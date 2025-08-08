{ pkgs }: {
  deps = [
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.python312Packages.uvicorn
    pkgs.nodejs-20_x
    pkgs.nodePackages.npm
    pkgs.git
    pkgs.bash
  ];
} 