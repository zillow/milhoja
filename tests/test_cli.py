from typing import Dict
from unittest.mock import Mock, patch
import pytest
from click.testing import CliRunner
from cookiecutter.exceptions import CookiecutterException
from pygit2 import Repository
from battenberg import cli
from battenberg.errors import BattenbergException, MergeConflictException


@pytest.fixture
def open_repository(installed_repo: Repository) -> Mock:
    with patch('battenberg.utils.open_repository') as open_repository:
        open_repository.return_value = installed_repo
        yield open_repository


@pytest.fixture
def Battenberg(open_repository: Mock) -> Mock:
    with patch('battenberg.cli.Battenberg') as Battenberg:
        yield Battenberg


@pytest.fixture
def obj() -> Dict:
    return {'target': '.'}


def test_help():
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help' in help_result.output


def test_install(Battenberg: Mock, obj: Dict):
    template = 'test-template'

    runner = CliRunner()
    result = runner.invoke(cli.install, [template], obj=obj)

    assert result.exit_code == 0
    assert result.output == ''
    Battenberg.return_value.install.assert_called_once_with(
        template, checkout=None, no_input=False
    )


def test_upgrade(Battenberg: Mock, obj: Dict):
    runner = CliRunner()
    result = runner.invoke(cli.upgrade, obj=obj)

    assert result.exit_code == 0
    assert result.output == ''
    Battenberg.return_value.upgrade.assert_called_once_with(
        checkout=None,
        context_file='.cookiecutter.json',
        merge_target=None,
        no_input=False
    )


def test_upgrade_raises_merge_conflicts(Battenberg: Mock, obj: Dict):
    Battenberg.return_value.upgrade.side_effect = MergeConflictException
    stdout = b'test-stdout'  # Use a bytestream as subprocess does.

    with patch('battenberg.cli.subprocess') as subprocess:
        completed_process = subprocess.run.return_value
        completed_process.stdout = stdout

        runner = CliRunner()
        result = runner.invoke(cli.upgrade, obj=obj)

        subprocess.run.assert_called_once_with(['git', 'status'], stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT)

    assert result.exit_code == 1
    assert stdout.decode('utf-8') in result.output
