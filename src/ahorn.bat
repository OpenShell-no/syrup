set AHORN_HOME=%~dp0
set JULIA_HOME=%AHORN_HOME%julia\bin
set JULIA_PKGDIR=%AHORN_HOME%juliapkg

"%JULIA_HOME%\julia.exe" "%JULIA_PKGDIR%\v0.6\Ahorn\src\run_ahorn.jl" %*