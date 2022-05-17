# Overview

A maintainer should be polite and respectful towards every member of the community in order to make opsdroid a great project for both newbies and veterans in open source.


- **Responsibilities**
  - Responding to issues and PRs (even just to say thanks and we'll look into it)
  - Reviewing and merging Pull Requests
  - Providing support on [matrix](https://app.element.io/#/room/#opsdroid-general:matrix.org)
  - Engaging in discussions on how to grow and shape opsdroid
  - Promote the project (blogging, tweeting, speaking at events, etc)
  - Make regular contributions and tackle old issues

- **Other important things**
  - Jacob, the creator of opsdroid, is the one to cut releases for now
  - If in doubt about a PR please mention @opsdroid/maintainers and ask for a review

## Reviewing and Merging Pull Requests
As a maintainer one of the tasks that you have to take on will be reviewing pull requests and merge them if it meets the criteria.

**Criteria for merging a PR**
  - You didn't write it yourself
  - The [PR template](https://github.com/opsdroid/opsdroid/tree/master/.github/PULL_REQUEST_TEMPLATE.md) criteria are met (has tests, is documented, etc)
  - The existing tests pass and coverage remains the same
  - It is related to an open issue
  - It moves us towards our [core aims](https://github.com/opsdroid/opsdroid/issues/1)

Depending on the pull request, coverage might drop a bit. If that is the case, as a maintainer you should ask that a test is created to bump the coverage back up. You might need to give some guidance as to how to properly test the code in the PR.

If a PR is not related to an open issue, then it's a proposal for the project. Jacob, the creator of opsdroid, and the community should give feedback and discuss the Pull Request either in the PR itself, an issue or in the [Matrix](https://app.element.io/#/room/#opsdroid-general:matrix.org) channel.

When merging a PR into opsdroid main branch you should take a few things into consideration.
- Use Squash and Merge option when merging a PR into opsdroid's master branch
- The title of the merge will be included in the release notes of a new opsdroid version, so the title should make sense.
- Remove unnecessary stuff from the description. If it takes 4 commits to get the tests to pass those lines should be deleted.

## Updating Requirements

Pyup-bot will check for new versions of the modules needed to run opsdroid that can be found on the requirements.txt when a new version is released, pyup-bot will automatically create the PR to update the modules.

Pyup-bot pull requests should be treated like any other pull request when merging them into opsdroid's master branch. As long the tests pass, you can squash and merge the PR into the master branch.

## Maintainer scripts

This project contains a directory called [`scripts`](https://github.com/opsdroid/opsdroid/tree/master/scripts) which are simple python scripts for use by maintainers when working on opsdroid. Each directory contains the script itself, a README and other supporting files. See the individual README files for more information.

_These scripts may have dependencies so you should run `pip install -r requirements_dev.txt` from the root of the project._
