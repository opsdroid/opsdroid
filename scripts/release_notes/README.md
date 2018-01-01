# Generate changelog/release notes

When cutting a release of opsdroid you need to include some release notes. This script generates them for you automatically.

The script assumes you have your git remotes configured with `origin` pointing to you fork of opsdroid and `upstream` pointing to the main opsdroid repo.

## Usage

```shell
python3 release_notes.py
```

## Output

```
Updating tags.
====================
<some git output>

Getting latest tag.
====================
Latest version is <some version>.

Generating changelog since <some version>.
====================
<changelog>
```
