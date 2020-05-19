# Release History

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
