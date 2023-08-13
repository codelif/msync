import sys

import click

import msync.ffstack as ffstack


@click.group()
def ffmpeg():
    """Manage ffmpeg binaries."""


@ffmpeg.command()
def check():
    """Check whether FFmpeg is installed."""
    installed = ffstack.is_installed()
    if installed:
        click.echo("FFmpeg is installed with parameter '%s'" % installed)
    else:
        click.echo("FFmpeg is not installed.")
        sys.exit(1)

    return installed


@ffmpeg.command()
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Install ffmpeg even if it is present.",
)
def install(force):
    """Installs FFmpeg."""
    if (not force) and (ffstack.is_installed()):
        click.echo("FFmpeg already installed.")
        return

    click.echo("Installing...")
    ffstack.install_ffstack()
    click.echo("FFmpeg successfully installed.")


@ffmpeg.command()
def where():
    """Where are FFmpeg binaries?"""
    dirname = ffstack.where()

    if dirname:
        click.echo(dirname)
    else:
        sys.exit(1)
