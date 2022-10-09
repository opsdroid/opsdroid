# Making a release

Occasionally the maintainers of the opsdroid project make a release, and
distribute it.  This document is the procedure they follow to do that.

## Background

When releasing, there are a couple of release artifacts which are built and distributed.

Currently opsdroid builds:

- A Python distribution on [pypi](https://pypi.org/project/opsdroid/)
- A Python distribution on [Conda Forge](https://github.com/conda-forge/opsdroid-feedstock)
- A container image on [Docker Hub](https://hub.docker.com/r/opsdroid/opsdroid/) and [Github container registry](https://github.com/opsdroid/opsdroid/pkgs/container/opsdroid)

The building and distributing is automated by Travis CI and run when a [release is created](https://help.github.com/articles/creating-releases/) on GitHub.

## Creating a release

### Testing

Before creating the release do some final local testing:

- Checkout master and run the `tox` suite locally.
- Run opsdroid and do some manual testing to ensure there are no glaring issues.

### Decide the next version number

As opsdroid follows [SemVer 2.0](http://semver.org/) (`major.minor.patch`) the version number increase will depend on what has changed since the previous release.

- If the release includes only bug fixes then only the `patch` will be incremented. (See [Backports](#Backports) section for making patches)
- If the release includes new features then the `minor` will be incremented and the `patch` will be reverted to `0`.
- If the release includes changes which break backward compatibility then the `major` will be incremented with the `minor` and `patch` being reverted to `0`. However this only applies once opsdroid is above `v1.0.0`.

Keep a note of what the new version will be as it will be needed later.

### Generate release text

We use [Release Drafter](https://github.com/marketplace/actions/release-drafter) to automatically draft our next release using GitHub Releases.

Release Drafter will create a draft release with the release notes automatically populated based on the titles of each PR that has been merged since the last release and grouped together using the labels `enhancement`, `bug` and `documentation`.

You need to review these notes to ensure all PRs have suitable titles and have been grouped successfully. If there are any issues then edit the release and manually make corrections.

Release Drafter also assumes the next release will be a minor version change, if this is not the case then update the release title and tag to match the version number you decided on earlier.

### Publish the release

Once you are happy with the release notes click "Publish release" on the draft.

This will result in a number of automated actions:

- The new [release tag](https://github.com/opsdroid/opsdroid/tags) will be created on GitHub.
- [Github CI](https://github.com/opsdroid/opsdroid/actions/) will build the [pypi distribution](https://pypi.python.org/pypi/opsdroid) and upload it.
- [Docker Hub](https://hub.docker.com/r/opsdroid/opsdroid/) and [Github container registry](https://github.com/opsdroid/opsdroid/pkgs/container/opsdroid) will build a new container image, create the [new release tag](https://hub.docker.com/r/opsdroid/opsdroid/tags/) and also update `latest` to point to this release.
- The @opsdroid [twitter account](https://twitter.com/opsdroid) will tweet that the release has been generated (via [IFTTT](https://ifttt.com)).

There are also the following manual actions which need to be performed:

- A PR will automatically be raised on the [opsdroid feedstock on Conda Forge](https://github.com/conda-forge/opsdroid-feedstock). This needs to be reviewed and merged.
