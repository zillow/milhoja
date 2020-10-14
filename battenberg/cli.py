import os
import sys
import logging
import subprocess
from typing import Optional
import click

from battenberg.core import Battenberg
from battenberg.utils import open_repository, open_or_init_repository
from battenberg.errors import MergeConflictException

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # noqa: E402


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('battenberg')
# Ensure we always receive debug messages.
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)


@click.group()
@click.option(
    '-O',
    default='.',
    help='Direct the output of battenberg to this path instead of the current working directory.',
    type=click.Path()
)
@click.option(
    '--verbose',
    default=False,
    is_flag=True,
    help='Enables the debug logging.'
)
@click.pass_context
def main(ctx, o: str, verbose: bool):
    """
    \f

    Script entry point for Battenberg commands.
    Arguments:
        ctx -- CLI context.
        o -- Path where to output battenberg to.
        verbose -- Enables debug logging
    """
    ctx.obj = dict()
    ctx.obj.update({
        'target': o,
        'verbose': verbose
    })

    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)


@main.command()
@click.argument('template')
@click.option(
    '--initial-branch',
    help='The initial branch name to use when creating a new repo',
    default=None
)
@click.option(
    '--checkout',
    help='branch, tag or commit to checkout from the remote template',
    default=None
)
@click.option(
    '--no-input', is_flag=True,
    help='Do not prompt for parameters and only use cookiecutter.json file content',
)
@click.pass_context
def install(ctx, template: str, initial_branch: Optional[str], **kwargs):
    """Create a new copy from the TEMPLATE repository.

    TEMPLATE is expected to be the URL of a git repository.
    """

    battenberg = Battenberg(open_or_init_repository(ctx.obj['target'], template, initial_branch))
    battenberg.install(template, **kwargs)


@main.command()
@click.option(
    '--checkout',
    help='branch, tag or commit to checkout from the remote template',
    default=None
)
@click.option(
    '--merge-target',
    help='A branch that the upgrade should be merged into',
    default=None
)
@click.option(
    '--context-file',
    default='.cookiecutter.json',
    help='Path where we can find the output of the cookiecutter template context',
    type=click.Path()
)
@click.option(
    '--no-input',
    is_flag=True,
    help='Do not prompt for parameters and only use .cookiecutter.json file content',
)
@click.pass_context
def upgrade(ctx, **kwargs):
    """Upgrade a existing copy of a template."""

    try:
        battenberg = Battenberg(open_repository(ctx.obj['target']))
        battenberg.upgrade(**kwargs)
    except MergeConflictException:
        # Just run "git status" in a subprocess so we don't have to re-implement the formatting
        # logic atop pygit2.
        completed_process = subprocess.run(['git', 'status'], stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT)
        click.echo(completed_process.stdout.decode('utf-8'))
        click.echo('Cannot merge upgrade automatically, please manually resolve the conflicts')
        sys.exit(1)  # Ensure we exit with a failure code.
