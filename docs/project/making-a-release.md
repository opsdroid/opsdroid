# Making a release

Occasionally the maintainers of the opsdroid project make a release, and
distribute it.  This document is the procedure they follow to do that.

## Background

When releasing, there are various release artifacts that need to be built,
and various places those release artifacts need to be uploaded to.

Currently opsdroid builds:
 * a python distribution for upload to pypi
 * ...

## Releasing

Do some pre-release tasks:
 * Check the test/coverage is ok for the candidate version
 * Check any milestones planned for this release have been achieved
 * Update the CHANGES.md file with relevant notes (TODO: start a CHANGES.md
   file)

Initiate builds

```shell
# This might include building a new thing to upload to pypi,
# or building new docker containers, or building a variety of other
# artifacts.  Hopefully this will be increasingly automated, perhaps by
# travis building artifacts for every commit, and we just pick the
# appropriate one to use.
echo do all the build things
```

Upload the builds. Note that in order to do this you need appropriate
credentials.  Currently only @jacobtomlinson can do this step.

```shell
# run the upload thing
```

Do some post-release tasks.
 * update the __version__ number in opsdroid/const.py to the number that
   will be used for the next release
 * Announce the release (TODO: modify this procedure to explicitly describe where those announcements belong)



