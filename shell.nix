{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  # Зависимости, необходимые для сборки
  buildInputs = [
    pkgs.gcc # Предоставляет g++
    pkgs.python3 # Предоставляет python-config и заголовочные файлы

    # Python и пакеты
    (pkgs.python3.withPackages (ps: [
      ps.flask
      ps.google-generativeai
      ps.pydantic
      ps.langchain
      ps.langchain-community
      ps.langchain-google-genai
      ps.faiss
      ps.numpy
      ps.grpcio-tools # На всякий случай
    ]))
  ];

  # Эта переменная окружения может помочь pip найти нужные библиотеки
  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
  '';
}
