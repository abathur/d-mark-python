{ lib
, fetchFromGitHub
, buildPythonPackage
, setuptools
, wheel
, version ? "unstable"
, src ? fetchFromGitHub {
    owner = "abathur";
    repo = "d-mark-python";
    rev = "4c0461046f1b7adf98757d06aa027c04a22e43e9";
    hash = "sha256-oeyLAcpLaCm46sLymATVdthbXQez5J1W/tGht8Obv90=";
  }
}:

buildPythonPackage {
  inherit src version;
  name = "d-mark-python";
  pyproject = true;

  nativeBuildInputs = [
    setuptools
    wheel
  ];
}
