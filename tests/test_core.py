from unittest.mock import patch
import pytest
from pygit2 import Reference, Repository
from battenberg.errors import TemplateConflictException, TemplateNotFoundException
from battenberg.core import Battenberg


def find_ref_from_message(repo: Repository, message: str, ref_name: str = 'master') -> Reference:
    return next(ref for ref in repo.references[f'refs/heads/{ref_name}'].log()
                if ref.message == message)


def test_install(repo: Repository, template_repo: Repository):
    battenberg = Battenberg(repo)
    battenberg.install(template_repo.workdir, no_input=True)

    assert battenberg.is_installed()
    # Ensure we have the appropriate branches we expect.
    assert not {'master', 'template'} - set(repo.listall_branches())

    # Ensure we have a valid structure for the template branch.
    template_oids = {ref.oid_new for ref in repo.references['refs/heads/template'].log()}
    template_commits = [repo[oid].message for oid in template_oids]
    assert template_commits == ['Prepared template installation']

    # Ensure we have valid merge commit from the template branch -> master.
    template_install_message = f'commit (merge): Installed template \'{template_repo.workdir}\''
    master_merge_ref = find_ref_from_message(repo, template_install_message)
    assert master_merge_ref
    # Ensure the merge commit was derived from the template branch.
    assert not template_oids - set(repo[master_merge_ref.oid_new].parent_ids)


def test_install_raises_template_conflict(repo: Repository, template_repo: Repository):
    # Create an existing template branch to force the error.
    repo.create_branch('template', repo[repo.head.target])

    battenberg = Battenberg(repo)

    with pytest.raises(TemplateConflictException):
        battenberg.install(template_repo.workdir)


def test_upgrade_raises_template_not_found(repo: Repository):
    repo.remotes.delete('origin')
    battenberg = Battenberg(repo)
    with pytest.raises(TemplateNotFoundException):
        battenberg.upgrade()


def test_upgrade_fetches_remote_template(installed_repo: Repository, template_repo: Repository):
    # installed_repo.remotes.create('origin', 'git@github.com:zillow/battenberg.git')
    template_oid = installed_repo.references.get('refs/heads/template').target
    installed_repo.branches.remote.create('origin/template', installed_repo[template_oid])
    installed_repo.branches.local.delete('template')

    # Couldn't work out a nice way to neatly construct remote branches, resort to mocking.
    with patch.object(installed_repo.references, 'get') as get_mock:
        get_mock.return_value.target = template_oid

        battenberg = Battenberg(installed_repo)
        battenberg.upgrade(checkout='upgrade', no_input=True)

        get_mock.assert_called_once_with('refs/remotes/origin/template')


def test_upgrade(installed_repo: Repository, template_repo: Repository):
    battenberg = Battenberg(installed_repo)
    battenberg.upgrade(checkout='upgrade', no_input=True)

    template_oids = {ref.oid_new for ref in installed_repo.references['refs/heads/template'].log()}
    template_commits = [installed_repo[oid].message for oid in template_oids]
    assert not set(template_commits) - {'Prepared template installation',
                                        'Prepared template upgrade'}

    template_upgrade_message = f'commit (merge): Upgraded template \'{template_repo.workdir}\''
    master_merge_ref = find_ref_from_message(installed_repo, template_upgrade_message)
    assert master_merge_ref
    # Ensure the merge commit was derived from the template branch.
    assert template_oids & set(installed_repo[master_merge_ref.oid_new].parent_ids)


def test_update_merge_target(installed_repo: Repository, template_repo: Repository):
    merge_target = 'target'
    battenberg = Battenberg(installed_repo)
    battenberg.upgrade(checkout='upgrade', no_input=True, merge_target=merge_target)

    template_upgrade_oid = next(
        ref.oid_new for ref in installed_repo.references['refs/heads/template'].log()
        if installed_repo[ref.oid_new].message == 'Prepared template upgrade'
    )

    template_upgrade_message = f'commit (merge): Upgraded template \'{template_repo.workdir}\''
    master_merge_ref = find_ref_from_message(installed_repo, template_upgrade_message,
                                             ref_name=merge_target)
    assert master_merge_ref
    # Ensure the merge commit on the merge target branch was derived from the template branch.
    assert template_upgrade_oid in set(installed_repo[master_merge_ref.oid_new].parent_ids)
