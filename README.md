# Battenberg

[![image](https://img.shields.io/pypi/v/battenberg.svg)](https://pypi.python.org/pypi/battenberg)
[![image](https://img.shields.io/travis/zillow/battenberg.svg)](https://github.com/zillow/battenberg/actions)

Battenberg is a tool built atop of [Cookiecutter](https://github.com/audreyr/cookiecutter) to keep Cookiecut projects
in sync with their parent templates. Under the hood, Battenberg relies on Git to manage the merging, diffing, and
conflict resolution story. The first goal of Battenberg is to provide an *upgrade* feature to Cookiecutter.

## Installation

We publish `battenberg` to [PyPI](https://pypi.org/project/battenberg/) for easy consumption.

```bash
pip install battenberg
```

If you're on Mac OS X or Windows please follow the [installation guides](https://www.pygit2.org/install.html#) in the `pygit2` documentation
as well as `battenberg` relies on `libgit2` which needs to be installed first. **Please install `libgit2 >= 1.0`.**

If you use SSH to connect to `git`, please also install `libssh2` **prior to installing `libgit2`!!** Most like you can do this via `brew install libssh2`
if you are on Mac OS X.

## Prerequistes

It is assumed that your cookiecutter template contains a `.cookiecutter.json` file at the root directory, or you can override its location by
passing in `--context-file`. Please use the [`jsonify`](https://github.com/cookiecutter/cookiecutter/pull/791) Jinja2 extension to dump the
`cookiecutter` template context to `.cookiecutter.json`.

**Tip:** One problem `battenberg` has that as divergence between the cookiecutter template and the project itself increase as will the volume of
conflicts needed to be manually resolved for each upgrade merge. To minimize these it is often advisable to fit templates with a
`generate_example` boolean flag which will disable including any example code, instead replacing implementation with a
[`pass`](https://docs.python.org/3/reference/simple_stmts.html#the-pass-statement) for example.

## Usage

Install a [Cookiecutter](https://github.com/audreyr/cookiecutter) template:

```bash
battenberg [-O <root path>] [--verbose] install [--checkout v1.0.0] [--initial-branch main] <cookiecutter template path/URL>
```

* `--checkout` - Specifies a target reference (branch, tag or commit) from the cookiecutter template repo, if not specified is it inferred from the default branch for the template repo.
* `-O` - Specifies an output folder path, defaults to the current directory.
* `--initial-branch` - The default branch for the newly created `git` repo, if not specified is it inferred from the default branch for the template repo.
* `--verbose` - Enables extra debug logging.

Upgrade your repository with last version of a template:

```bash
battenberg upgrade [--checkout v1.0.0] [--no-input] [--merge-target <branch, tag or commit>] [--context-file <context filename>]
```

* `--checkout` - Specifies a target reference (branch, tag or commit) from the cookiecutter template repo, if not specified is it inferred from the default branch for the template repo.
* `--no-input` - Read in the template context from `--context-file` instead of asking the `cookiecutter` template questions again.
* `--merge-target` - Specify where to merge the eventual template updates.
* `--context-file` - Specifies where to read in the template context from, defaults to `.cookiecutter.json`.

    *Note: `--merge-target` is useful to set if you are a template owner but each cookiecut repo is owned independently. The value you pass*
    *to `--merge-target` should be the source branch for a PR that'd target `main` in the cookiecut repo so they can approve any changes.*

## Onboarding existing cookiecutter projects

A great feature of `battenberg` is that it's relatively easy to onboard existing projects you've already cookiecut from an existing template.
To do this you need to follow the `battenberg install` instructions above but use the `-O` output to specify the directory of the existing
project and it'll create you a new `template` branch and attempt to merge just like an upgrade operation.

Once you've completed your first merge from `template` -> `main` you can then follow the `battenberg upgrade` instructions as though it was
generated using `battenberg` initially.

## High-level design

At a high level `battenberg` attempts to provide a continuous history between the upstream template project and the cookiecut project. It does this by maintaining a disjoint `template`
branch which `battenberg` attempts to keep in sync with the upstream template, it therefore will contain no project-specific changes beyond replacing the template values. Then changes
to the `template` are incorporated into the `main` and other branches via a `git merge --allow-unrelated-histories` command for each template update pulled in. This merge commit
should be used to resolve any conflicts between the upstream template and the specialized project.

![A new project in battenberg](https://github.com/zillow/battenberg/raw/main/img/new.png)

*This shows the repo structure immediately after running a `battenberg install <template>` command*

![An updated project in battenberg](https://github.com/zillow/battenberg/raw/main/img/updated.png)

*This shows the repo structure immediately after running a `battenberg upgrade` command on the previously installed project*

## Development

To get set up run:

```bash
python3 -m venv env
source env/bin/activate

# Install in editable mode so you get the updates propagated.
pip install -e .

# If you want to be able to run tests & linting install via:
pip install -e ".[dev]"
```

Then to actually perform any operations just use the `battenberg` command which should now be on your `$PATH`.

To run tests:

```bash
pytest
```

To run linting:

```bash
flake8 --config flake8.cfg battenberg
```

## Releasing a new version to PyPI

**Reminder to update [`HISTORY.md`](./HISTORY.md) with a summary of any updates, especially breaking changes.**

We utilize GitHub Actions to deploy to PyPI. We've limited it to just publish on `git tags`. To release run:

```bash
# Change to the appropriate commit you want to base the release on.
vi battenberg/__init__.py  # Update the version string.
git tag <version>
git push origin <version>
```

Then watch the build for any errors, eventually it should appear on the [`battenberg` PyPI](https://pypi.org/project/battenberg/) project.

## FAQ

* I got an error like `_pygit2.GitError: unsupported URL protocol`, how do I fix this?

    Likely you're using a `git` URL with `ssh` and have installed `pygit2` without access to the underlying `libssh2`
    library. To test this run:

    ```bash
    $ python -c "import pygit2; print(bool(pygit2.features & pygit2.GIT_FEATURE_SSH))"
    False
    ```

    To remedy this run:

    ```bash
    $ pip uninstall pygit2
    ...
    # Hopefully you have this, but this will install the compiler toolchain for OS X.
    $ xcode-select --install
    ...
    $ brew install libssh2
    ...
    $ brew install libgit2
    ...
    # The python wheels for Mac OS X for pygit2 are not built with SSH support by default so tell pip
    # to install pygit2 from source.
    $ pip install pygit2 --no-binary pygit2
    ...
    # Finally test out to ensure pygit2 picks up the SSH features.
    $ python -c "import pygit2; print(bool(pygit2.features & pygit2.GIT_FEATURE_SSH))"
    True
    ```

* Why are you using a new `.cookiecutter.json` pattern instead of using the [`replay` pattern](https://cookiecutter.readthedocs.io/en/latest/advanced/replay.html)?

    Frankly the implementation was quite convoluted to get the intentions of these features to align. With the `.cookiecutter.json` approach
    we're intended for template state to live at the project level instead of at the user level which the `replay` functionality defaults to.
    Overriding that behaviour, whilst possible was convoluted in the current `cookiecutter` API and would require upstream changes so instead
    we decided against trying to align these features.

* Why `battenberg`?

    A tribute to the shoulders this project stands on, [`cookiecutter`](https://github.com/cookiecutter/cookiecutter) &
    [`milhoja`](https://github.com/rmedaer/milhoja), and [a tasty cake](https://en.wikipedia.org/wiki/Battenberg_cake) in its own right.

## Credits

[Original code](https://github.com/rmedaer/battenberg) written by [Raphael Medaer](https://github.com/rmedaer) from an [original
idea](https://github.com/cookiecutter/cookiecutter/issues/784) of [Abdó Roig-Maranges](https://github.com/aroig).

## License

Free software: Apache Software License 2.0
