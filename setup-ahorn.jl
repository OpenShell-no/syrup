
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
