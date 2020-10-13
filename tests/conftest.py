import os
import stat
from distutils.dir_util import copy_tree, remove_tree
import tarfile
import tempfile
from types import TracebackType
from typing import List, Optional, Type
import pytest
from pygit2 import Repository, init_repository
from battenberg.core import Battenberg


class TemporaryRepository:
    """
    Constructs a git repo from the tests/data/testrepo.tar file in the /tmp directory.

    Taken from pygit2 tests: https://github.com/libgit2/pygit2/blob/master/test/utils.py
    """

    def __enter__(self) -> 'TemporaryRepository':
        name = 'testrepo'
        repo_path = os.path.join(os.path.dirname(__file__), 'data', f'{name}.tar')
        self.temp_dir = tempfile.mkdtemp()
        temp_repo_path = os.path.join(self.temp_dir, name)
        tar = tarfile.open(repo_path)
        tar.extractall(self.temp_dir)
        tar.close()
        return temp_repo_path

    def __exit__(self, type: Optional[Type[BaseException]], value: Optional[BaseException],
                 traceback: TracebackType):
        if os.path.exists(self.temp_dir):
           remove_tree(self.temp_dir)


@pytest.fixture
def repo() -> Repository:
    with TemporaryRepository() as repo_path:
        yield Repository(repo_path)


def copy_template(repo: Repository, name : str, commit_message: str, parents: List[str] = None) -> str:
    template_path = os.path.join(os.path.dirname(__file__), 'data', name)
    # Use distuils implementation instead of shutil to allow for copying into
    # a destination with existing files. See: https://stackoverflow.com/a/31039095/724251
    copy_tree(template_path, repo.workdir)

    # Stage the template changes
    repo.index.add_all()
    repo.index.write()
    tree = repo.index.write_tree()
    # Construct a commit with the staged changes.
    return repo.create_commit(
        None,
        repo.default_signature,
        repo.default_signature,
        commit_message,
        tree,
        parents or []
    )


@pytest.fixture
def template_repo() -> Repository:
    repo_path = tempfile.mkdtemp()
    repo = init_repository(repo_path, initial_head='main')

    # Copy template contents into a temporary repo for each test.
    main_commit_id = copy_template(repo, 'template', 'Prepared template installation')
    repo.branches.local.create('main', repo[main_commit_id])
    repo.checkout('refs/heads/main')

    # Construct a new "upgrade" branch which battenberg can target during upgrade.
    upgrade_commit_id = copy_template(
        repo,
        'upgrade-template',
        'Prepared upgrade-template installation',
        parents=[main_commit_id]
    )
    repo.branches.local.create('upgrade', repo[upgrade_commit_id])

    return repo


@pytest.fixture
def installed_repo(repo: Repository, template_repo: Repository) -> Repository:
    battenberg = Battenberg(repo)
    battenberg.install(template_repo.workdir, no_input=True)
    return repo
