import hashlib
import urllib
import os
import sys
import subprocess
import shutil
import stat
import fnmatch

from PIL import Image
import requests

CHECKSUM_TYPE = "sha256"

ICON_SIZES = [16, 32, 48, 64, 96, 128, 256]

TEMP_DIR = "tmp"

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

def cleanBuild(builddir):
    print("Cleaning build directory...")
    if os.path.exists(builddir):
        for path, _dirs, files in os.walk(builddir):
            for name in files:
                pathname = os.path.join(path, name)
                # Silly git readonly files.
                os.chmod(pathname, stat.S_IWRITE)
                os.unlink(pathname)
        shutil.rmtree(builddir, onerror=lambda func, path, exec_info: print("WARNING: Failed to delete ", path, exec_info))

def cleanArtifacts(artifactdir):
    print("Cleaning artifact directory...")
    if os.path.exists(artifactdir):
        shutil.rmtree(artifactdir, onerror=lambda func, path, exec_info: print("WARNING: Failed to delete ", path, exec_info))

def copySrc(src_dir, build_dir):
    print("Copying src/*...")
    for name in os.listdir(src_dir):
        src = os.path.join(src_dir, name)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(build_dir, name))
        else:
            shutil.copy(src, build_dir)

def makeIco(icon, name, build_dir):
    "Generates .ico file from .png"
    print("Generating .ico file...")
    im = Image.open(icon)
    fn = "{name}.ico".format(name)
    im.save(os.path.join(build_dir, fn), sizes=[(x,x) for x in ICON_SIZES])
    return fn

def compileNSISTemplate(build_dir, artifact_dir, executables, **kwargs):
    "Generates NSIS script from jinja2 template"
    print("Generating NSIS script...")
    import jinja2
    loader = jinja2.PackageLoader(__package__)
    env = jinja2.Environment(loader=loader, autoescape=False, undefined=jinja2.StrictUndefined)

    template = env.get_template("generic.nsi.j2")

    install_files = []
    install_dirs = []
    install_size = 0
    install_executables = []
    for path, dirs, files in os.walk(build_dir):
        for name in files:
            itempath = os.path.join(path, name)
            outpath = os.path.relpath(itempath, build_dir)

            install_files.append(dict(
                input = itempath,
                output = outpath,
            ))

            install_size += os.stat(itempath).st_size

            for pat in executables:
                if fnmatch.fnmatch(outpath, pat) and outpath not in install_executables:
                    install_executables.append(outpath)
        
        for name in dirs:
            itempath = os.path.join(path, name)
            relitempath = os.path.relpath(itempath, build_dir)
            install_dirs.append(relitempath)

    template_variables = {
        'files': install_files,
        'dirs': install_dirs,
        'outfile': os.path.join(artifact_dir, "${APPNAME}-${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}-setup.exe"),
        'size': install_size,
        'executables': install_executables,
    }
    template_variables.update(kwargs)

    nsis_script = os.path.join(build_dir, "generic.nsi")
    with open(nsis_script, "w") as fh: # TODO: Temp file name.
        template.stream(**template_variables).dump(fh)
    return nsis_script

def NSISBuildInstaller(nsi_script, artifact_dir):
    print("Building NSIS installer...")

    os.makedirs(artifact_dir, exist_ok=True)

    # http://nsis.sourceforge.net/Docs/Chapter3.html#usage
    command = [TOOLS_NSIS, "/NOCD", "/INPUTCHARSET", "UTF8", "/P3", "/V3", nsi_script]
    print(cmd(command, stdout=sys.stdout, stderr=sys.stderr, encoding="utf8"))
