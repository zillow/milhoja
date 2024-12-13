from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from battenberg.errors import InvalidRepositoryException, KeypairMissingException
from battenberg.utils import open_repository, open_or_init_repository, construct_keypair, ALGORITHMS


@pytest.fixture
def Repository() -> Mock:
    with patch('battenberg.utils.Repository') as Repository:
        yield Repository


@pytest.fixture
def discover_repository() -> Mock:
    with patch('battenberg.utils.discover_repository') as discover_repository:
        yield discover_repository


@pytest.fixture
def init_repository() -> Mock:
    with patch('battenberg.utils.init_repository') as init_repository:
        yield init_repository


@pytest.fixture
def Keypair() -> Mock:
    with patch('battenberg.utils.Keypair') as Keypair:
        yield Keypair


@pytest.fixture
def MockPath() -> Mock:
    with patch('battenberg.utils.Path') as MockPath:
        yield MockPath


def test_open_repository(Repository: Mock, discover_repository: Mock):
    path = 'test-path'
    assert open_repository(path) == Repository.return_value
    Repository.assert_called_once_with(discover_repository.return_value)
    discover_repository.assert_called_once_with(path)


def test_open_repository_raises_on_invalid_path():
    path = 'test-path'
    with pytest.raises(InvalidRepositoryException, match=f'{path} is not a valid repository path.'):
        open_repository(path)


def test_open_or_init_repository_opens_repo(Repository: Mock, discover_repository: Mock):
    path = 'test-path'
    template = 'test-template'
    assert open_or_init_repository(path, template) == Repository.return_value
    Repository.assert_called_once_with(discover_repository.return_value)
    discover_repository.assert_called_once_with(path)


def test_open_or_init_repository_initializes_repo(init_repository: Mock, Repository: Mock,
                                                  discover_repository: Mock):
    discover_repository.side_effect = Exception('No repo found')

    path = 'test-path'
    template = 'test-template'
    initial_branch = 'test-initial_branch'
    repo = init_repository.return_value
    assert open_or_init_repository(path, template, initial_branch) == repo
    init_repository.assert_called_once_with(path, initial_head=initial_branch)
    init_repository.return_value.create_commit.assert_called_once_with(
        'HEAD',
        repo.default_signature,
        repo.default_signature,
        'Initialized repository',
        repo.index.write_tree.return_value,
        []
    )


@patch('battenberg.utils.subprocess')
def test_open_or_init_repository_initializes_repo_with_inferred_initial_branch(
        subprocess: Mock, init_repository: Mock, Repository: Mock, discover_repository: Mock):
    initial_branch = 'refs/heads/main'
    subprocess.run.return_value.stdout = f'ref: {initial_branch}    HEAD'
    discover_repository.side_effect = Exception('No repo found')

    path = 'test-path'
    template = 'test-template'
    repo = init_repository.return_value
    assert open_or_init_repository(path, template) == repo
    repo.references['HEAD'].set_target.assert_called_once_with(initial_branch)


@pytest.mark.parametrize('stdout', ('', 'invalid-symref'))
@patch('battenberg.utils.subprocess')
def test_open_or_init_repository_initializes_repo_with_invalid_remote_branches(
        subprocess: Mock, init_repository: Mock, Repository: Mock, discover_repository: Mock,
        stdout: str):
    subprocess.run.return_value.stdout = stdout
    discover_repository.side_effect = Exception('No repo found')

    path = 'test-path'
    template = 'test-template'
    repo = init_repository.return_value
    assert open_or_init_repository(path, template) == repo


def test_construct_keypair_defaults(Keypair: Mock, MockPath: Mock, tmp_path: Path):
    MockPath.return_value = tmp_path
    public_key_path = tmp_path / 'id_rsa.pub'
    public_key_path.touch()
    private_key_path = tmp_path / 'id_rsa'
    private_key_path.touch()
    construct_keypair()
    Keypair.assert_called_with('git', public_key_path,
                               private_key_path, '')


@pytest.mark.parametrize('algorithm', ALGORITHMS.values())
def test_construct_keypair(Keypair: Mock, tmp_path: Path, algorithm: dict[str, Path]):
    public_key_path = tmp_path / algorithm['public']
    public_key_path.touch()
    private_key_path = tmp_path / algorithm['private']
    private_key_path.touch()
    passphrase = 'test-passphrase'
    construct_keypair(tmp_path, passphrase)
    Keypair.assert_called_with('git', public_key_path, private_key_path, passphrase)


def test_construct_keypair_missing_key(MockPath: Mock, tmp_path: Path):
    MockPath.return_value = tmp_path
    with pytest.raises(KeypairMissingException):
        construct_keypair()
