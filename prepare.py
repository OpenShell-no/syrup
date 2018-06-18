import requests
import hashlib
import urllib
import os
import sys
import subprocess
import shutil
import stat
from PIL import Image

JULIA_VERSION = (0, 6, 3)
CHECKSUM_TYPE = "sha256"

JULIA_BIN_FILENAME = "julia-{v[0]}.{v[1]}.{v[2]}-win64.exe".format(v=JULIA_VERSION)
JULIA_BIN = "https://julialang-s3.julialang.org/bin/winnt/x64/{v[0]}.{v[1]}/{file}".format(v=JULIA_VERSION, file=JULIA_BIN_FILENAME)
JULIA_CHECKSUMS = "https://julialang-s3.julialang.org/bin/checksums/julia-{v[0]}.{v[1]}.{v[2]}.{checksum}".format(v=JULIA_VERSION, checksum=CHECKSUM_TYPE)

LOGO_FILE = "logo-1024-a.png"
ICON_SIZES = [16, 32, 48, 64, 96, 128, 256]

JULIA_JUNK = [
    "$PLUGINSDIR",
    "Uninstall.exe",
]

TEMP_DIR = "tmp"
BUILD_DIR = "build"
SRC_DIR = "src"
ARTIFACT_DIR = "artifacts"

TOOLS_7ZIP = "./tools/7z"
TOOLS_NSIS = "D:/Software/NSIS/Bin/makensis.exe"

def download_file(url, target=None, verbose=False):
    # https://stackoverflow.com/a/16696317
    # NOTE the stream=True parameter
    cs = hashlib.new(CHECKSUM_TYPE)
    req = requests.get(url, stream=True)

    url_fn = os.path.basename(urllib.parse.urlparse(req.url).path)

    if target is None:
        outpath = os.path.realpath(url_fn)
    elif os.path.isdir(target) or target[-1] in ['/', '\\']:
        outpath = os.path.join(target, url_fn)
    else:
        outpath = target

    os.makedirs(os.path.dirname(outpath), exist_ok=True)

    with open(outpath, 'wb') as fh:
        for chunk in req.iter_content(chunk_size=None):
            if chunk: # filter out keep-alive new chunks
                fh.write(chunk)
                cs.update(chunk)
        fh.flush()
    return (outpath, cs.hexdigest())

def parse_checksum_file(content):
    result = {}
    for line in content.split('\n'):
        if not line.strip(): continue
        hex, fn = line.split(maxsplit=1)
        result[fn] = hex
    return result

def cmd(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, encoding=None):
    #print(args)
    p = subprocess.Popen(args, stdout=stdout, stderr=stderr)
    if p.stdout is not None:
        if encoding is not None:
            p.stdout.read().decode(encoding)
        return p.stdout.read()
    else:
        p.wait()
        return p.returncode

def p7zip_list(fn):
    data = cmd([TOOLS_7ZIP, "l", "-slt", "-sccUTF-8", fn]).decode("utf-8")

    files = []

    data = data.replace('\r\n', '\n')

    _crap, archivedata = data.split('\n--\n', 1)
    _headers, filedata = archivedata.split('\n----------\n', 1)
    filelist = filedata.split('\n\n\n')[0].split('\n\n')

    for fileinfo in filelist:
        if not fileinfo.strip(): continue
        
        fi = dict([[y.strip() for y in x.split('=', 1)] for x in fileinfo.strip().split('\n')])

        if fi.get('Attributes') == 'D': continue # Directory

        files.append({
            'name': fi.get('Path'),
            'size': int(fi.get('Size')),
            'crc': fi.get('CRC'),
        })
    
    return files

def p7zip_open_file(fn, name):
    p = subprocess.Popen(
        [TOOLS_7ZIP, "e", "-so", fn],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    return p.stdout

def p7zip_extract_file(fn, name, target=None):
    with p7zip_open_file(fn, name) as zfh:
        if target is None:
            outpath = os.path.realpath(name)
        elif os.path.isdir(target) or target[-1] in ['/', '\\']:
            outpath = os.path.join(target, os.path.basename(name))
        else:
            outpath = target

        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        with open(outpath, "wb") as ofh:
            ofh.write(zfh.read())

    return outpath

def p7zip_extract(fn, target=None):
    if target is None:
        outpath = "."
    else:
        outpath = target
        os.makedirs(target, exist_ok=True)
    
    p = subprocess.Popen(
        [TOOLS_7ZIP, "x", "-o{}".format(outpath), fn],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    p.wait()
    return outpath
    


def checksum_file(path, checksum_type=CHECKSUM_TYPE):
    cs = hashlib.new(checksum_type)
    with open(path, "rb") as fh:
        data = fh.read(1_048_576)
        while data:
            cs.update(data)
            data = fh.read(1_048_576)
    return cs.hexdigest()


def downloadJulia():
    outfn = os.path.join(TEMP_DIR, JULIA_BIN_FILENAME)
    csfile = "{}.{}".format(outfn, CHECKSUM_TYPE)

    if os.path.exists(csfile) and os.path.exists(outfn):
        cs = parse_checksum_file(open(csfile).read()).get(JULIA_BIN_FILENAME)
        if cs == checksum_file(outfn):
            print("Cached Julia installer ok.")
            return outfn

    checksums = parse_checksum_file(requests.get(JULIA_CHECKSUMS).text)
    os.makedirs(os.path.dirname(outfn), exist_ok=True)

    print("Downloading Julia installer file...")
    fn, dlcs = download_file(JULIA_BIN, outfn)
    
    cs = checksums.get(os.path.basename(fn))

    assert dlcs == cs, "Checksum verification on  download `{}` failed. `{}` != `{}`".format(JULIA_BIN, dlcs, cs)

    with open(csfile, "w", encoding="utf-8") as fh:
        fh.write(cs)
        fh.write("  ")
        fh.write(os.path.basename(fn))
        fh.write("\n")
    print("Download of `{}` completed and verified.".format(fn))

    return outfn

def cleanBuild():
    print("Cleaning build directory...")
    if os.path.exists(BUILD_DIR):
        for path, dirs, files in os.walk(BUILD_DIR):
            for name in files:
                pathname = os.path.join(path, name)
                # Silly git readonly files.
                os.chmod(pathname, stat.S_IWRITE)
                os.unlink(pathname)
        shutil.rmtree(BUILD_DIR, onerror=lambda func, path, exec_info: print("WARNING: Failed to delete ", path, exec_info))

def cleanArtifacts():
    print("Cleaning artifact directory...")
    shutil.rmtree("artifacts", onerror=lambda func, path, exec_info: print("WARNING: Failed to delete ", path, exec_info))

def extractJulia():
    print("Extracting Julia...")
    jbin1 = downloadJulia()
    jbin2 = p7zip_extract_file(jbin1, "julia-installer.exe", target=TEMP_DIR)

    jbuild = os.path.join(BUILD_DIR, "julia")

    if os.path.exists(jbuild):
        shutil.rmtree(jbuild)
    
    p7zip_extract(jbin2, jbuild)

    for name in JULIA_JUNK:
        p = os.path.join(jbuild, name)

        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.exists(p):
            os.remove(p)

    print(jbin2)

def copySrc():
    print("Copying src/*...")
    for name in os.listdir(SRC_DIR):
        src = os.path.join(SRC_DIR, name)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(BUILD_DIR, name))
        else:
            shutil.copy(src, BUILD_DIR)

def makeIco():
    "Generates .ico file from .png"
    print("Generating .ico file...")
    im = Image.open(LOGO_FILE)
    im.save(os.path.join(BUILD_DIR, "ahorn.ico"), sizes=[(x,x) for x in ICON_SIZES])

def compileNSISTemplate():
    "Generates NSIS script from jinja2 template"
    print("Generating NSIS script...")
    import jinja2
    loader = jinja2.FileSystemLoader('templates')
    env = jinja2.Environment(loader=loader, autoescape=False)

    template = env.get_template("Ahorn.nsi.j2")

    install_files = []
    install_dirs = []
    for path, dirs, files in os.walk(BUILD_DIR):
        for name in files:
            itempath = os.path.join(path, name)
            install_files.append(dict(
                input = itempath,
                output = os.path.relpath(itempath, BUILD_DIR),
            ))
        
        for name in dirs:
            itempath = os.path.join(path, name)
            relitempath = os.path.relpath(itempath, BUILD_DIR)
            install_dirs.append(relitempath)

    template_variables = {
        'files': install_files,
        'dirs': install_dirs,
        'outfile': os.path.join(ARTIFACT_DIR, "setup-${APPNAME}-${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}.exe"),
    }

    with open("Ahorn.nsi", "w") as fh:
        template.stream(**template_variables).dump(fh)

def NSISBuildInstaller():
    print("Building NSIS installer...")

    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    # http://nsis.sourceforge.net/Docs/Chapter3.html#usage
    print(cmd([TOOLS_NSIS, "/INPUTCHARSET", "UTF8", "/P3", "/V3", "Ahorn.nsi"], stdout=sys.stdout, stderr=sys.stderr, encoding="utf8"))

def setupAhorn():
    print("Running Ahorn setup...")
    return cmd([os.path.join(BUILD_DIR, "julia.bat"), "setup-ahorn.jl"], stdout=None, stderr=None)

if __name__ == "__main__":
    print(cleanArtifacts())
    print(cleanBuild())
    print(extractJulia())
    print(copySrc())
    print(setupAhorn())
    print(makeIco())
    print(compileNSISTemplate())
    print(NSISBuildInstaller())