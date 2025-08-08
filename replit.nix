{ pkgs }: {
  deps = [
    pkgs.python39
    pkgs.python39Packages.pip
    pkgs.python39Packages.uvicorn
    pkgs.nodejs-18_x
    pkgs.nodePackages.npm
    pkgs.git
    pkgs.bash
  ];
} 