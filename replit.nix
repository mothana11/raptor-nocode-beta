{ pkgs }:

{
  deps = [
    # ---- Python 3.11 + pip + uvicorn -----------------------------
    (pkgs.python3.withPackages (ps: with ps; [ pip uvicorn ]))

    # ---- Node 18 + npm (22.11’s latest) --------------------------
    pkgs.nodejs-18_x       # Node runtime
    pkgs.nodePackages.npm  # npm command

    # ---- Misc utilities -----------------------------------------
    pkgs.git
    pkgs.bashInteractive
  ];
}
