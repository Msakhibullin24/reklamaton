{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    (pkgs.python3.withPackages (ps: [
      ps.google-generativeai
      ps.flask
    ]))
  ];
}
