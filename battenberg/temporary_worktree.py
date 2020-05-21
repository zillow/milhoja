import os
import shutil
import tempfile
import logging
from types import TracebackType
from typing import Optional, Type

from pygit2 import Repository, Worktree
from battenberg.errors import (
    RepositoryEmptyException,
    WorktreeConflictException,
    WorktreeException
)


logger = logging.getLogger(__name__)


class TemporaryWorktree:

    def __init__(self, upstream: Repository, name: str, empty: bool = True):
        if name in upstream.list_worktrees():
            raise WorktreeConflictException(name)

        self.upstream = upstream
        self.name = name
        # Create the worktree working directory in the /tmp directory so it's out of the way.
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, name)
        self.worktree = None
        self.repo = None
        self.empty = empty

    def __enter__(self) -> 'TemporaryWorktree':
        logger.debug(f'Creating temporary worktree at {self.path}.')

        if self.upstream.head_is_unborn:
            raise RepositoryEmptyException()

        try:
            self.worktree: Worktree = self.upstream.add_worktree(self.name, self.path)
        except ValueError as error:
            raise WorktreeException(self.name, self.path) from error

        # Construct a separate repository instance so we can commit to a different copy and merge
        # between branches.
        self.repo = Repository(self.worktree.path)

        if self.empty:
            for entry in self.repo[self.repo.head.target].tree:
                if os.path.isdir(os.path.join(self.path, entry.name)):
                    shutil.rmtree(os.path.join(self.path, entry.name))
                else:
                    os.remove(os.path.join(self.path, entry.name))

        logger.debug(f'Successfully created temporary worktree at {self.path}.')

        return self

    def __exit__(self, type: Optional[Type[BaseException]], value: Optional[BaseException],
                 traceback: TracebackType):
        logger.debug(f'Removing temporary worktree at {self.path}.')
        shutil.rmtree(self.tmp)

        # Prune temp worktree
        if self.worktree is not None:
            self.worktree.prune(True)

        self.upstream.lookup_branch(self.name).delete()

        logger.debug(f'Successfully removed temporary worktree at {self.path}.')
