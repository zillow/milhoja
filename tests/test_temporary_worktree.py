import os
from unittest.mock import patch
import pytest
from battenberg.temporary_worktree import TemporaryWorktree
from battenberg.errors import (
    RepositoryEmptyException,
    WorktreeConflictException,
    WorktreeException
)


@pytest.fixture
def worktree_name():
    return 'test-worktree_name'


@pytest.fixture
def worktree_path(tmpdir):
    return os.path.join(str(tmpdir), 'worktree')


def test_raises_worktree_conflict(repo, worktree_name, worktree_path):
    repo.add_worktree(worktree_name, worktree_path)

    with pytest.raises(WorktreeConflictException) as e:
        with TemporaryWorktree(repo, worktree_name):
            pass

    assert str(e.value) == f'Worktree {worktree_name} already exists'


def test_raises_repository_empty(repo, worktree_name):
    # Initially set the HEAD pointer to a value without a backing reference.
    repo.set_head('refs/heads/test-empty')

    with pytest.raises(RepositoryEmptyException) as e:
        with TemporaryWorktree(repo, worktree_name):
            pass


@patch('battenberg.temporary_worktree.tempfile.mkdtemp')
def test_raises_worktree_error(mkdtemp, repo, worktree_name, worktree_path):
    mkdtemp.return_value = worktree_path
    
    with patch.object(repo, 'add_worktree') as add_worktree:
        add_worktree.side_effect = ValueError('Error adding new worktree')
        with pytest.raises(WorktreeException) as e:
            with TemporaryWorktree(repo, worktree_name):
                pass
        
        add_worktree.assert_called_once_with(worktree_name,
                                             os.path.join(worktree_path, worktree_name))


@pytest.mark.parametrize('empty,dir_contents', (
    (True, {'.git'}),
    (False, {'.gitignore', '.git', 'hello.txt'})
))
def test_initializes_empty_worktree(repo, worktree_name, empty, dir_contents):
    # Loop over all the entries in the unstaged tree.
    get_tree_entries = lambda r: {entry.name for entry in r[r.head.target].tree}
    assert get_tree_entries(repo) == {'.gitignore', 'hello.txt'}

    with TemporaryWorktree(repo, worktree_name, empty=empty) as tmp_worktree:
        # Not an easy way to compare apples to apples here as it constructs the worktree
        # and immediately empties it in the same function. Some work todo here to make
        # this a little cleaner in the future I think.
        assert set(os.listdir(tmp_worktree.path)) == dir_contents
