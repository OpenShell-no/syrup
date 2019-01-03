set AHORN_HOME=%~dp0
set JULIA_HOME=%AHORN_HOME%julia\bin
set JULIA_PKGDIR=%AHORN_HOME%juliapkg
echo %CD%
"%JULIA_HOME%\julia.exe" %*