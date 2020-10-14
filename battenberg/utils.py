import os
import logging
import getpass
from typing import Optional, Union
from pygit2 import (discover_repository, init_repository, Keypair, RemoteCallbacks, Repository,
                    UserPass)


logger = logging.getLogger(__name__)


def open_repository(path: str) -> Repository:
    return Repository(discover_repository(path))


def open_or_init_repository(path: str, template: str, initial_branch: Optional[str] = None):
    try:
        return open_repository(path)
    except Exception:
        # Not found any repo, let's make one.
        pass

    repo = init_repository(path, initial_head=initial_branch)

    # Mirror the default HEAD of the template repo if client hasn't explicitly provided it.
    if not initial_branch:
        repo = set_initial_branch(repo, template)

    repo.create_commit(
        'HEAD',
        repo.default_signature,
        repo.default_signature,
        'Initialized repository',
        repo.index.write_tree(),
        []
    )
    return repo


def get_credentials(template: str) -> Union[Keypair, UserPass]:
    if 'https' in template:
        username = getpass.getuser()
        password = getpass.getpass()
        return UserPass(username, password)
    elif 'git@' in template:
        return construct_keypair()
    else:
        raise ValueError(f'Unsupported template URL type: {template}')


def set_initial_branch(repo: Repository, template: str) -> Repository:
    remote_name = 'template'
    try:
        import pdb; pdb.set_trace()
        credentials = get_credentials(template)
    except ValueError as e:
        logger.debug(e)
        return repo

    repo.remotes.create(remote_name, template)
    remotes = repo.remotes[remote_name].ls_remotes(
        callbacks=RemoteCallbacks(credentials=credentials))
    for remote in remotes:
        if remote['name'] == 'HEAD':
            # We found the remote HEAD, now set the found symbolic_ref (ie. the default branch
            # name), as the default branch for the newly created repo.
            default_branch_name = remote['symref_target'].split()[-1]

            # TODO AIPO-999 Actually take the symref_target and create a new HEAD branch and
            # rearrange references.
            print('symref_target: ', remote['symref_target'], default_branch_name)
            break
    repo.remotes.delete(remote_name)

    return repo


def construct_keypair(public_key_path: str = None, private_key_path: str = None,
                      passphrase: str = '') -> Keypair:
    ssh_path = os.path.join(os.path.expanduser('~'), '.ssh')
    if not public_key_path:
        public_key_path = os.path.join(ssh_path, 'id_rsa.pub')
    if not private_key_path:
        private_key_path = os.path.join(ssh_path, 'id_rsa')
    return Keypair("git", public_key_path, private_key_path, passphrase)
