{ pkgs }:

{
  deps = [
    # --- Python 3.11 with the packages you need ---------------
    (pkgs.python3.withPackages (ps: with ps; [
      pip          # brings in the `pip` CLI
      uvicorn       # runtime dep for your FastAPI app
    ]))

    # --- Node 20 & the npm CLI -------------------------------
    pkgs.nodejs_20              # interpreter
    pkgs.nodePackages.npm       # npm command

    # --- Misc tools you asked for ----------------------------
    pkgs.git
    pkgs.bashInteractive
  ];
}
