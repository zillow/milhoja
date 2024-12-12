import logging
import re
import subprocess
from typing import Optional
from pygit2 import discover_repository, init_repository, Keypair, Repository
from battenberg.errors import InvalidRepositoryException, KeypairException
from pathlib import Path

logger = logging.getLogger(__name__)


def open_repository(path: Path) -> Repository:
    try:
        repo_path = discover_repository(path)
    except Exception as e:
        # Looks like exceptions raised in the C code from pygit2 are all of type Exception so
        # we're forced to rely on the message to interpret.
        if 'No repo found' in str(e):
            raise InvalidRepositoryException(path)
        raise

    if not repo_path:
        raise InvalidRepositoryException(path)

    return Repository(repo_path)


def open_or_init_repository(path: Path, template: str, initial_branch: Optional[str] = None):
    try:
        return open_repository(path)
    except InvalidRepositoryException:
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


ALGORITHMS = {
    "ED25519": {
        "public": "id_ed25519.pub",
        "private": "id_ed25519"
    },
    "ED25519_SK": {
        "public": "id_ed25519_sk.pub",
        "private": "id_ed25519_sk"
    },
    "ECDSA_SK": {
        "public": "id_ecdsa_sk.pub",
        "private": "id_ecdsa_sk"
    },
    "RSA": {
        "public": "id_rsa.pub",
        "private": "id_rsa"
    }
}


def construct_keypair(public_key_path: Path = None, private_key_path: Path = None,
                      passphrase: str = '') -> Keypair:
    ssh_path = Path('~/.ssh').expanduser()
    for algorithm in ALGORITHMS.values():
        public_key_path = public_key_path or (ssh_path / algorithm['public'])
        private_key_path = private_key_path or (ssh_path / algorithm['private'])
        if public_key_path.exists() and private_key_path.exists():
            break
        public_key_path = None
        private_key_path = None
    else:
        raise KeypairException(f'Could not find keypair in {ssh_path}',
                               f'Possible options include: {ALGORITHMS}')

    return Keypair("git", public_key_path, private_key_path, passphrase)
