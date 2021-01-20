class BattenbergException(Exception):
    """
    Abstract Battenberg generic exception.
    """
    pass


class TemplateConflictException(BattenbergException):
    """
    Error raised when a template is already installed.
    """

    def __init__(self):
        super().__init__('Template already installed')


class WorktreeException(BattenbergException):
    """
    Error raised when worktree could not be initialized.
    """

    def __init__(self, worktree_name: str, worktree_path: str):
        super().__init__(
            f'Worktree \'{worktree_name}\' could not be initialized in path \'{worktree_path}\''
        )


class WorktreeConflictException(BattenbergException):
    """
    Error raised when worktree already exist.
    """

    def __init__(self, worktree_name: str):
        super().__init__(f'Worktree {worktree_name} already exists')


class TemplateNotFoundException(BattenbergException):
    """
    Error raised when template could not be found.
    """

    def __init__(self):
        super().__init__('Template could not be found')


class RepositoryEmptyException(BattenbergException):
    """
    Error raised when Git repository is unborn.
    """

    def __init__(self):
        super().__init__('Target repository is empty')


class MergeConflictException(BattenbergException):
    """
    Error raised when we cannot merge the template commit with the target branch.
    """
    pass


class InvalidRepositoryException(BattenbergException):
    """
    Error raised when Git repository is invalid.
    """

    def __init__(self, path: str):
        super().__init__(f'{path} is not a valid repository path.')
