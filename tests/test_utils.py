import os
from unittest.mock import patch
import pytest
from battenberg.utils import open_repository, open_or_init_repository, construct_keypair


@pytest.fixture
def Repository():
    with patch('battenberg.utils.Repository') as Repository:
        yield Repository


@pytest.fixture
def discover_repository():
    with patch('battenberg.utils.discover_repository') as discover_repository:
        yield discover_repository


def test_open_repository(Repository, discover_repository):
    path = 'test-path'
    assert open_repository(path) == Repository.return_value
    Repository.assert_called_once_with(discover_repository.return_value)
    discover_repository.assert_called_once_with(path)


def test_open_or_init_repository_opens_repo(Repository, discover_repository):
    path = 'test-path'
    assert open_or_init_repository(path) == Repository.return_value
    Repository.assert_called_once_with(discover_repository.return_value)
    discover_repository.assert_called_once_with(path)


@patch('battenberg.utils.init_repository')
def test_open_or_init_repository_initializes_repo(init_repository, Repository, discover_repository):
    discover_repository.side_effect = Exception('No repo found')

    path = 'test-path'
    repo = init_repository.return_value
    assert open_or_init_repository(path) == repo
    init_repository.assert_called_once_with(path)
    init_repository.return_value.create_commit.assert_called_once_with(
        'HEAD',
        repo.default_signature,
        repo.default_signature,
        'Initialized repository',
        repo.index.write_tree.return_value,
        []
    )


@patch('battenberg.utils.Keypair')
def test_construct_keypair_defaults(Keypair):
    construct_keypair()
    user_home = os.path.expanduser('~')
    Keypair.assert_called_once_with('git', f'{user_home}/.ssh/id_rsa.pub',
                                    f'{user_home}/.ssh/id_rsa', '')


@patch('battenberg.utils.Keypair')
def test_construct_keypair(Keypair):
    public_key_path = 'test-public_key_path'
    private_key_path = 'test-private_key_path'
    passphrase = 'test-passphrase'
    construct_keypair(public_key_path, private_key_path, passphrase)
    Keypair.assert_called_once_with('git', public_key_path, private_key_path, passphrase)
