
println("""
======================
Initializing package repository
======================
""")
Pkg.init()

install_or_update(url::String, pkg::String) = try 
    if Pkg.installed(pkg) !== nothing
        println("Updating $pkg...")
        Pkg.update(pkg)
    end
catch err
    println("Installing $pkg...")
    Pkg.clone(url, pkg)
end


println("""
======================
Installing packages
======================
""")

install_or_update("https://github.com/CelestialCartographers/Maple.git", "Maple")
install_or_update("https://github.com/CelestialCartographers/Ahorn.git", "Ahorn")

Pkg.add("HTTP")

println("""
======================
Building packages
======================
""")

cp(joinpath(Pkg.dir("Ahorn"), "src", "run_ahorn.jl"), joinpath(ENV["AHORN_HOME"], "ahorn.jl"), remove_destination=true)

Pkg.build()

for pkg in collect(keys(Pkg.installed()))
    if !isdefined(Symbol(pkg)) && pkg != "Compat.jl"
        info("Importing $(pkg)...")
        try (@eval import $(Symbol(pkg))) catch end
    end
end