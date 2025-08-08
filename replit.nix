{ pkgs }:

{
  deps = [
    # ---- Python 3.11 + pip + uvicorn ---------------------------------
    (pkgs.python3.withPackages (ps: with ps; [ pip uvicorn ]))

    # ---- Node 18 + npm (22.11’s newest) ------------------------------
    pkgs.nodejs-18_x       # Node runtime
    pkgs.nodePackages.npm  # npm CLI

    # ---- Utilities ---------------------------------------------------
    pkgs.git
    pkgs.bashInteractive   # gives you an interactive bash
  ];
}
