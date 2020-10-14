import os
import logging
import re
import subprocess
from typing import Optional
from pygit2 import discover_repository, init_repository, Keypair, Repository


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
        set_initial_branch(repo, template)

    repo.create_commit(
        'HEAD',
        repo.default_signature,
        repo.default_signature,
        'Initialized repository',
        repo.index.write_tree(),
        []
    )
    return repo


def set_initial_branch(repo: Repository, template: str):
    completed_process = subprocess.run(
        ['git', 'ls-remote', '--symref', template, 'HEAD'],
        stdout=subprocess.PIPE, encoding='utf-8')
    found_refs = completed_process.stdout.split('\n')

    if found_refs:
        match = re.match(r"^ref: (?P<initial_branch>(\w+)/(\w+)/(\w+))\s*HEAD", found_refs[0])
        if match:
            initial_branch = match.group('initial_branch')
            logger.debug(f'Found remote default branch: {initial_branch}')
            repo.references['HEAD'].set_target(initial_branch)


def construct_keypair(public_key_path: str = None, private_key_path: str = None,
                      passphrase: str = '') -> Keypair:
    ssh_path = os.path.join(os.path.expanduser('~'), '.ssh')
    if not public_key_path:
        public_key_path = os.path.join(ssh_path, 'id_rsa.pub')
    if not private_key_path:
        private_key_path = os.path.join(ssh_path, 'id_rsa')
    return Keypair("git", public_key_path, private_key_path, passphrase)
