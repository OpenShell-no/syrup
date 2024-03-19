Installation
============
```
pip install git+https://github.com/OpenShell-no/syrup.git
```

Usage
=====
```
syrup build --name="TestApp" --company="TestingInc" --version=0.0.1 --src-dir=testinput
```

See `syrup build --help` for details.

Developement
============
```
git clone https://github.com/OpenShell-no/syrup.git
pip install --editable ./syrup
```

External dependencies
=====================
 * Git (For installing from git) - https://git-scm.com/
 * Python >= 3.5 - https://python.org/
 * NSIS >= 3.04 - https://nsis.sourceforge.io/Download \
   The following packages works for Mint 19 "tessa" (Ubuntu 18.04 "bionic"):
    - https://packages.ubuntu.com/disco/amd64/nsis/download
    - https://packages.ubuntu.com/disco/all/nsis-common/download
