# Release History

## 0.5.2 (2024-11-12)

- Update to pygit2 usage to enable usage of newer versions of the package while also maintaining backwards compatibility.

## 0.5.1 (2023-08-08)

- Update python version to 3.9+

## 0.5.0 (2023-03-31)

- Update python version to 3.7+

## 0.4.1 (2021-01-25)

- Suppress stacktrace logging when hook exits unsuccessfully (See [#23](https://github.com/zillow/battenberg/pull/23))
- Ensure we're compatible with updated `Repository.__init__` constructor (See [#23](https://github.com/zillow/battenberg/pull/23))

## 0.4.0 (2020-10-13)

- Remove `master` as the default `git` target branch terminology to promote equity and belonging. Instead rely on remote HEAD to infer default branch naming convention.
- Add in `--initial-branch` optional argument to `battenberg install` to specify the initial branch to create when initializing a new project.

## 0.3.0 (2020-05-29)

- Update `pygit2` dependency to `>= 1.0`, can now rely on `libgit2 >= 1.0` too. (See [#18](https://github.com/zillow/battenberg/pull/18))
- Add in better debug logging (See [#16](https://github.com/zillow/battenberg/pull/16))

## 0.2.3 (2020-05-19)

- Refactor removal of top-level directory after cookiecutting to avoid collisions. (See [#15](https://github.com/zillow/battenberg/pull/15))
- Set upper limit on pygit2 dependency (See [#14](https://github.com/zillow/battenberg/pull/14))

## 0.2.2 (2020-01-29)

- Fix regression that stopped injecting context when upgrading.

## 0.2.1 (2020-01-29)

- Cleans up error message when merging results in conflicts. (See [#13](https://github.com/zillow/battenberg/pull/13))

## 0.2.0 (2019-10-29)

- Adds in remote fetching of `origin/template` branch during upgrades. (See [#12](https://github.com/zillow/battenberg/pull/12))

## 0.1.1 (2019-10-17)

- Revert back to relying on mainline `cookiecutter` instead of Zillow fork. (See [#9](https://github.com/zillow/battenberg/pull/9))

## 0.1.0 (2019-10-10)

- Add in support for reading template context from `.cookiecutter.json`. (See [#2](https://github.com/zillow/battenberg/pull/2))
- Add in `--merge-target` CLI option. (See [#4](https://github.com/zillow/battenberg/pull/4))
- Expanded test coverage, added in CI/CD via Travis CI. (See [#8](https://github.com/zillow/battenberg/pull/8))

Prior to v0.1.0 `battenberg` was developed under the [`milhoja`](https://github.com/rmedaer/milhoja) project.
