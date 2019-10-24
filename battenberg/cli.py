import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # noqa: E402


import logging
import click
from cookiecutter.cli import validate_extra_context
from cookiecutter.exceptions import CookiecutterException
from battenberg.core import Battenberg
from battenberg.utils import open_repository, open_or_init_repository
from battenberg.errors import BattenbergException


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
def main(ctx, o, verbose):
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
@click.argument('extra_context', nargs=-1, callback=validate_extra_context)
@click.option(
    '--checkout',
    help='branch, tag or commit to checkout',
    default='master'
)
@click.option(
    '--no-input', is_flag=True,
    help='Do not prompt for parameters and only use cookiecutter.json file content',
)
@click.pass_context
def install(ctx, template, **kwargs):
    try:
        battenberg = Battenberg(open_or_init_repository(ctx.obj['target']))
        battenberg.install(template, **kwargs)
    except (BattenbergException, CookiecutterException) as error:
        raise click.ClickException from error


@main.command()
@click.argument('extra_context', nargs=-1, callback=validate_extra_context)
@click.option(
    '--checkout',
    help='branch, tag or commit to checkout',
    default='master'
)
@click.option(
    '--merge-target',
    help='A branch that the upgrade should be merged into.',
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
    try:
        battenberg = Battenberg(open_repository(ctx.obj['target']))
        battenberg.upgrade(**kwargs)
    except (BattenbergException, CookiecutterException) as error:
        raise click.ClickException from error
