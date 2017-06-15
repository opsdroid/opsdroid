export

all: test

test:
	tox

release-notes:
	git log `git describe --tags --abbrev=0`..HEAD --oneline | cut -d' ' -f 2-
