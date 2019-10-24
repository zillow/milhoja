import os
from pygit2 import Repository, discover_repository, init_repository, Keypair


def open_repository(path):
    return Repository(discover_repository(path))


def open_or_init_repository(path):
    try:
        return open_repository(path)
    except Exception:
        # Not found any repo, let's make one.
        pass

    repo = init_repository(path)
    repo.create_commit(
        'HEAD',
        repo.default_signature,
        repo.default_signature,
        'Initialized repository',
        repo.index.write_tree(),
        []
    )
    return repo


def construct_keypair(public_key_path: str = None, private_key_path: str = None,
                      passphrase: str = '') -> Keypair:
    ssh_path = os.path.join(os.path.expanduser('~'), '.ssh')
    if not public_key_path:
        public_key_path = os.path.join(ssh_path, 'id_rsa.pub')
    if not private_key_path:
        private_key_path = os.path.join(ssh_path, 'id_rsa')
    return Keypair("git", public_key_path, private_key_path, passphrase)
