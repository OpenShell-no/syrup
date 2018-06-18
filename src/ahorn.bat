set AHORN_HOME=%~dp0
set JULIA_HOME=%AHORN_HOME%julia\bin
set JULIA_PKGDIR=%AHORN_HOME%juliapkg

%JULIA_HOME%\julia.exe %AHORN_HOME%ahorn.jl %*