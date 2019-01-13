@echo off
set AHORN_HOME=%~dp0
set JULIA_HOME=%AHORN_HOME%julia\bin
set JULIA_PKGDIR=%AHORN_HOME%juliapkg

echo !!! Running Pkg.build...
"%JULIA_HOME%\julia.exe" -e "Pkg.build()"

echo !!! Precompiling modules...
"%JULIA_HOME%\julia.exe" -e "for pkg in collect(keys(Pkg.installed())) if !isdefined(Symbol(pkg)) && pkg != join(`Compat.jl`.exec); info(join(`Importing\ $(pkg)...`.exec)); try (@eval import $(Symbol(pkg))) catch end end end"
