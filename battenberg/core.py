import sys
import os
import json
import logging
import shutil
import tempfile
from typing import Any, Dict, Optional

from pygit2 import (
    RemoteCallbacks,
    Repository,
    GIT_MERGE_ANALYSIS_UP_TO_DATE,
    GIT_MERGE_ANALYSIS_FASTFORWARD,
    GIT_MERGE_ANALYSIS_NORMAL
)
from cookiecutter.main import cookiecutter
from cookiecutter.exceptions import FailedHookException
from battenberg.errors import (
    BattenbergException,
    MergeConflictException,
    TemplateConflictException,
    TemplateNotFoundException
)
from battenberg.temporary_worktree import TemporaryWorktree
from battenberg.utils import construct_keypair


WORKTREE_NAME = 'templating'
TEMPLATE_BRANCH = 'template'
logger = logging.getLogger(__name__)


class Battenberg:

    def __init__(self, repo: Repository):
        self.repo = repo

    def is_installed(self) -> bool:
        """Determines in the repo is already using battenberg.

        Returns:
            A boolean on whether the repo was already using battenberg to manage itself.
        """
        return TEMPLATE_BRANCH in self.repo.listall_branches()

    def _fetch_remote_template(self):
        # First try to pull it from the remote origin/TEMPLATE_BRANCH
        keypair = construct_keypair()
        self.repo.remotes['origin'].fetch([TEMPLATE_BRANCH],
                                          callbacks=RemoteCallbacks(credentials=keypair))
        self.repo.references.create(
            f'refs/heads/{TEMPLATE_BRANCH}',
            self.repo.references.get(f'refs/remotes/origin/{TEMPLATE_BRANCH}').target
        )

    def _cookiecut(self, cookiecutter_kwargs: dict, worktree: TemporaryWorktree):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger.debug(f"Cookiecutting {cookiecutter_kwargs['template']} into {tmpdir}")
            try:
                cookiecutter(
                    replay=False,
                    overwrite_if_exists=True,
                    output_dir=tmpdir,
                    **cookiecutter_kwargs
                )
            except FailedHookException as e:
                # Suppress stacktrace for known hook error to ensure it is easy for user to diget.
                logging.error(e)
                sys.exit(1)

            # Cookiecutter guarantees a single top-level directory after templating.
            logger.debug('Shifting directories down a level')
            top_level_dir = os.path.join(tmpdir, os.listdir(tmpdir)[0])
            for f in os.listdir(top_level_dir):
                shutil.move(os.path.join(top_level_dir, f), worktree.path)

    def _get_context(self, context_file: str, base_path: str = None) -> Dict[str, Any]:
        with open(os.path.join(base_path or self.repo.workdir, context_file)) as f:
            return json.load(f)

    def _merge_template_branch(self, message: str, merge_target: str = None):
        branch = self.repo.lookup_branch(TEMPLATE_BRANCH)

        merge_target_ref = 'HEAD'
        if merge_target is not None:
            # If we have a merge target, ensure we have that branch and have switched to it
            # before continuing with merging.
            merge_target_ref = f'refs/heads/{merge_target}'
            if merge_target not in self.repo.listall_branches():
                self.repo.branches.local.create(
                    merge_target, self.repo.get(
                        self.repo.head.target))
            self.repo.checkout(merge_target_ref)

        analysis, _ = self.repo.merge_analysis(branch.target, merge_target_ref)

        if analysis & GIT_MERGE_ANALYSIS_UP_TO_DATE:
            logger.info('The branch is already up to date, no need to merge.')

        elif analysis & GIT_MERGE_ANALYSIS_FASTFORWARD or analysis & GIT_MERGE_ANALYSIS_NORMAL:
            # Ensure we're merging into the right
            self.repo.checkout(merge_target_ref)

            # Let's merge template changes using --allow-unrelated-histories. This will allow
            # the disjoint histories to be merged successfully. If you want to manually replicate
            # this option please run:
            #
            #     "git merge --allow-unrelated-histories template"
            #
            logger.debug('Forcing merge of template branch into target branch.')
            self.repo.merge(branch.target)

            # If there is a conflict we should error and let the user manually
            # resolve it.
            if self.repo.index.conflicts is not None:
                raise MergeConflictException(
                    f'Cannot merge the template commit ({branch.target}) with the current HEAD '
                    f'({self.repo.head}). Please resolve them manually and run \'git commit\' '
                    'to merge'
                )

            # Stage all the changes for commit.
            tree = self.repo.index.write_tree()

            # Add the commit back to the HEAD (normally the main branch unless --merge-target
            # is passed).
            self.repo.create_commit(
                'HEAD',
                self.repo.default_signature,
                self.repo.default_signature,
                message,
                tree,
                [self.repo.head.target, branch.target]
            )

            # Ensure we're not keeping any lingering metadata state before trying to merge the tmp
            # worktree into the main HEAD.
            self.repo.state_cleanup()
            self.repo.checkout('HEAD')

            logger.debug('Successfully applied changes.')
        else:
            raise BattenbergException(
                f'Unknown merge analysis result: {analysis}')

    def install(self, template: str, checkout: Optional[str] = None, no_input: bool = False):
        """Creates a fresh template install within the supplied repo.

        Generates a template using the provided context, or invokes the questionnaire to elicit it.

        Args:
            template: The path (either local or git) to the template project. It must follow
                the cookiecutter format to be compatible with battenberg.
            checkout: The new state to pull from the template, normally this will be a git tag on
                the template repo.
            no_input: Whether to ask the user to answer the template questions again or take the
                default answers from the templates "cookiecutter.json".

        Raises:
            MergeConflictException: Thrown when an upgrade results in merge conflicts between the
                template branch and the merge-target branch.
            TemplateConflictException: When the repo already contains a template branch. If you
                encounter this please run "battenberg upgrade" instead.
        """

        # Assert template branch doesn't exist or raise conflict
        if self.is_installed():
            raise TemplateConflictException()

        # Create temporary worktree
        with TemporaryWorktree(self.repo, WORKTREE_NAME) as worktree:
            cookiecutter_kwargs = {
                'template': template,
                'checkout': checkout,
                'no_input': no_input
            }
            self._cookiecut(cookiecutter_kwargs, worktree)
            logger.debug(
                f"Successfully cookiecut {cookiecutter_kwargs['template']} into {worktree.path}.")

            # Stage changes
            worktree.repo.index.add_all()
            worktree.repo.index.write()
            tree = worktree.repo.index.write_tree()

            # Create an orphaned commit
            oid = worktree.repo.create_commit(
                None,
                worktree.repo.default_signature,
                worktree.repo.default_signature,
                'Prepared template installation',
                tree,
                []
            )
            commit = self.repo.get(oid)

            # Create a branch which target orphaned commit
            branch = self.repo.create_branch(TEMPLATE_BRANCH, commit)

            # Optionally, set worktree HEAD to this branch (useful for debugging)
            # Optional ? Obviously the tmp worktree will be removed in __exit__
            worktree.repo.set_head(branch.name)

        # Let's merge our changes into HEAD
        logger.debug('Merging changes into HEAD.')
        self._merge_template_branch(f'Installed template \'{template}\'')

    def upgrade(self, checkout: Optional[str] = None, no_input: bool = True,
                merge_target: Optional[str] = None, context_file: str = '.cookiecutter.json'):
        """Updates a repo using the found template context.

        Generates and applies any updates from the current repo state to the template state defined
        by "checkout". It does this by reading the existing template context state defined within
        "context_file" and using that to pull in any new updates.

        Args:
            checkout: The new state to pull from the template, normally this will be a git tag on
                the template repo.
            no_input: Whether to ask the user to answer the template questions again or take the
                answers from the template context defined in "context_file".
            merge_target: A branch to checkout other than the current HEAD. Useful if you're
                upgrading a project you do not directly own.
            context_file: Where battenberg should look to read the template context.

        Raises:
            MergeConflictException: Thrown when an upgrade results in merge conflicts between the
                template branch and the merge-target branch.
            TemplateNotFoundException: When the repo does not already contain a template branch. If
                you encounter this please run "battenberg install" instead.
        """

        if not self.is_installed():
            try:
                self._fetch_remote_template()
            except KeyError as e:
                # Cannot find the origin remote branch.
                logger.error(e)
                raise TemplateNotFoundException() from e

        # Get last context used to apply template
        context = self._get_context(context_file)
        logger.debug(f'Found context: {context}')
        # Fetch template information, this is normally the git:// URL.
        template = context['_template']
        logger.debug(f'Found template: {template}')

        # Create temporary EMPTY worktree
        with TemporaryWorktree(self.repo, WORKTREE_NAME) as worktree:
            # Set HEAD to template branch
            branch = worktree.repo.lookup_branch(TEMPLATE_BRANCH)
            worktree.repo.set_head(branch.name)

            cookiecutter_kwargs = {
                'template': template,
                'checkout': checkout,
                'extra_context': context,
                'no_input': no_input
            }
            self._cookiecut(cookiecutter_kwargs, worktree)

            # Stage changes
            worktree.repo.index.read()
            worktree.repo.index.add_all()
            worktree.repo.index.write()
            tree = worktree.repo.index.write_tree()

            # Create commit on the template branch
            oid = worktree.repo.create_commit(
                'HEAD',
                worktree.repo.default_signature,
                worktree.repo.default_signature,
                'Prepared template upgrade',
                tree,
                [worktree.repo.head.target]
            )
            commit = worktree.repo.get(oid)

        # Make template branch ref to created commit, see https://github.com/libgit2/pygit2/blob/master/CHANGELOG.md#1150-2024-05-18
        self.repo.lookup_branch(TEMPLATE_BRANCH).set_target(str(commit.id))

        # Let's merge our changes into HEAD
        self._merge_template_branch(
            f'Upgraded template \'{template}\'', merge_target)
