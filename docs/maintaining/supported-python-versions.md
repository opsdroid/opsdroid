# Supported Python versions

In opsdroid we follow [NEP 29](https://numpy.org/neps/nep-0029-deprecation_policy.html) to decide which versions of Python to support at any given time.

NEP29 states that we should support any Python version released in the previous 42 months. This effectively covers the previous two releases of Python (the release cycle is 18 months) and includes an additional six months to account for any fluctuations in release dates. It gives the community time to adopt new releases.

In addition to this we will also endeavour to support new minor versions of Python within 6 months of their release.

## Support table

| Version | Release Date   | Start Support | End Support   | Status              |
|---------|----------------|---------------|---------------|---------------------|
|  3.11   | 2022-10-24     | March 2025    | April 2026    | Supported           |
|  3.12   | 2023-10-02     | March 2025    | April 2027    | Supported           |
|  3.13   | 2024-10-07     | March 2025    | April 2028    | Supported           |

_If you think this table may be out of date please help by raising a [Pull Request](https://github.com/opsdroid/opsdroid/edit/main/docs/maintaining/supported-python-versions.md) to fix it._

## Python version upgrades

Developers who wish to update the supported Python versions need to keep the following files in sync:
- https://github.com/opsdroid/opsdroid/blob/main/.github/workflows/ci.yml#L16
- https://github.com/opsdroid/opsdroid/blob/main/.github/workflows/ci.yml#L63
- https://github.com/opsdroid/opsdroid/blob/main/tox.ini#L7-L9
- https://github.com/opsdroid/opsdroid/blob/main/tox.ini#L49
- https://github.com/opsdroid/opsdroid/blob/main/Dockerfile#L1
- https://github.com/opsdroid/opsdroid/blob/main/.readthedocs.yml#L6
- https://github.com/opsdroid/opsdroid/blob/main/setup.cfg#L41
- and of course this documentation page