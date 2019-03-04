import os
from collections import namedtuple

import click

from .functions import (
    cleanArtifacts,
    cleanBuild,
    copySrc,
    makeIco,
    compileNSISTemplate,
    NSISBuildInstaller,
)

Version = namedtuple('Version', ['major', 'minor', 'build'])
Version.__str__ = lambda self: "{self.major}.{self.minor}.{self.build}".format(self=self)

@click.group()
@click.version_option()
def cli():
    pass

@cli.command()
@click.option('--build-dir', default="build", type=click.Path(file_okay=False))
@click.option('--artifact-dir', default="artifacts", type=click.Path(file_okay=False))
@click.option('--clean-artifacts/--no-clean-artifacts', default=False)
def clean(build_dir, artifact_dir, clean_artifacts, **kwargs):
    if clean_artifacts:
        cleanArtifacts(artifact_dir)
    cleanBuild(build_dir)

def validate_version(ctx, param, value):
    try:
        return Version(*[int(x) if x else 0 for x in value.split('.')])
    except:
        raise click.BadParameter('version must be in major.minor.build format. (1.0.0)')

@cli.command()
@click.option('--version', callback=validate_version, default="0.0.0", help="Version number of build (major.minor.build).")
@click.option('--name', required=True, help="Application name.")
@click.option('--company', required=True, help="Company name.")
@click.option('--description', help="Application description.")

@click.option('--license', default=None, type=click.Path(exists=True, dir_okay=False), help="Path to license file (rtf or txt with CRLF line endings).")
@click.option('--icon', default=None, type=click.Path(exists=True, dir_okay=False), help="Path to image to use as icon.")

@click.option('--clean/--no-clean', 'do_clean', default=True, help="Clean before building (default: true).")
@click.option('--clean-artifacts/--no-clean-artifacts', default=False, help="Clean artifacts (default: false).")

@click.option('--build-dir', default="build", type=click.Path(file_okay=False), help="Path to build (temporary) directory.")
@click.option('--artifact-dir', default="artifacts", type=click.Path(file_okay=False), help="Path to installer output directory.")
@click.option('--src-dir', default="src", type=click.Path(file_okay=False, exists=True), help="Path to application files to create installer from.")
@click.option('--executable', '-e', multiple=True, default=["*.exe"], help="Path of executables to create startmenu shortcuts to. Relative to src-dir. Can be passed multiple times. (default: *.exe)")

@click.option('--help-url', help="Help URL to display in 'Add/Remove Programs'. mailto: is allowed.")
@click.option('--update-url', help="Update URL to display in 'Add/Remove Programs'. mailto: is allowed.")
@click.option('--website-url', help="Website(about) URL to display in 'Add/Remove Programs'. mailto: is allowed.")

@click.pass_context
def build(ctx, do_clean, version, name, company, description, license, icon, build_dir, artifact_dir, src_dir, clean_artifacts, help_url, update_url, website_url, executable):
    click.echo("Building {} v{}...".format(name, version))
    if do_clean:
        ctx.forward(clean)
    
    os.makedirs(build_dir, exist_ok=True)

    copySrc(src_dir=src_dir, build_dir=build_dir)
    
    if icon:
        icon = makeIco(icon=icon, name=name, build_dir=build_dir)
    
    nsi_script = compileNSISTemplate(
        build_dir=build_dir, artifact_dir=artifact_dir,
        executables=executable,
        version=version,
        icon=icon, license=license,
        icon_path=os.path.join(build_dir, icon) if icon else None,
        name=name, company=company,
        description=description,
        help_url=help_url, update_url=update_url, website_url=website_url,
    )

    NSISBuildInstaller(nsi_script=nsi_script, artifact_dir=artifact_dir)

if __name__ == "__main__":
    # pylint:disable=unexpected-keyword-arg
    cli(auto_envvar_prefix='SYRUP')
