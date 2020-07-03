<h6 align=center>
<img src="https://github.com/opsdroid/style-guidelines/raw/master/logos/logo-light.png" alt="Opsdroid Logo" style="margin-top:-100px;margin-bottom:-50px;"/>
</h6>

<h1 align=center>opsdroid</h1>

<h4 align=center>An open source chat-ops bot framework</h4>

<p align=center>
<a href="https://pypi.python.org/pypi"><img src="https://img.shields.io/pypi/v/opsdroid.svg" alt="Current version of pypi" /></a>
<a href="https://travis-ci.org/opsdroid/opsdroid"><img src="https://img.shields.io/travis/opsdroid/opsdroid/master.svg?logo=travis" alt="Build Status" /></a>
<a href="https://ci.appveyor.com/project/opsdroid/opsdroid/branch/master"><img src="https://img.shields.io/appveyor/ci/opsdroid/opsdroid/master.svg?logo=appveyor" alt="Build status" /></a>
<a href="https://codecov.io/gh/opsdroid/opsdroid"><img src="https://img.shields.io/codecov/c/github/opsdroid/opsdroid.svg" alt="codecov" /></a>
<a href="https://bettercodehub.com/"><img src="https://bettercodehub.com/edge/badge/opsdroid/opsdroid?branch=master" alt="BCH compliance" /></a>
<a href="https://pyup.io/repos/github/opsdroid/opsdroid/"><img src="https://pyup.io/repos/github/opsdroid/opsdroid/shield.svg" alt="Updates" /></a>
<a href="https://hub.docker.com/r/opsdroid/opsdroid/builds/"><img src="https://img.shields.io/docker/build/opsdroid/opsdroid.svg" alt="Docker Build" /></a>
<a href="https://hub.docker.com/r/opsdroid/opsdroid/"><img src="https://img.shields.io/microbadger/image-size/opsdroid/opsdroid.svg" alt="Docker Image" /></a>
<a href="https://microbadger.com/#/images/opsdroid/opsdroid"><img src="https://img.shields.io/microbadger/layers/opsdroid/opsdroid.svg" alt="Docker Layers" /></a>
<a href="http://opsdroid.readthedocs.io/en/stable/?badge=stable"><img src="https://img.shields.io/readthedocs/opsdroid/latest.svg" alt="Documentation Status" /></a>
<a href="https://riot.im/app/#/room/#opsdroid-general:matrix.org"><img src="https://img.shields.io/matrix/opsdroid-general:matrix.org.svg?logo=matrix" alt="Matrix Chat" /></a>
<a href="#backers"><img src="https://opencollective.com/opsdroid/backers/badge.svg" alt="Backers on Open Collective" /></a>
<a href="#sponsors"><img src="https://opencollective.com/opsdroid/sponsors/badge.svg" alt="Sponsors on Open Collective" /></a>
<a href="https://www.codetriage.com/opsdroid/opsdroid"><img src="https://www.codetriage.com/opsdroid/opsdroid/badges/users.svg" alt="Open Source Helpers" /></a>
</p>

---

<p align="center">
  <a href="https://docs.opsdroid.dev/en/stable/installation.html#quickstart">Quick Start</a> •
  <a href="https://docs.opsdroid.dev">Documentation</a> •
  <a href="https://medium.com/opsdroid">Blog</a> •
  <a href="https://riot.im/app/#/room/#opsdroid-general:matrix.org">Community</a>
</p>

---

This framework allows you to take events from chat services and other sources and execute Python functions (skills) based on their contents. Those functions can be anything you like, from simple conversational responses to running complex tasks. As events pass through opsdroid they can be augmented using a range of different parsing services, from Natural Language Understanding (NLU) to sentiment analysis, to object recognition. This extra information allows you to make better decisions about how you handle those events and what actions you trigger as a result.

Help support opsdroid in one click by pressing [![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Check%20out%20opsdroid,%20an%20awesome%20open%20source%20chatbot%20framework%20written%20in%20Python.&url=https://opsdroid.github.io/&via=opsdroid&hashtags=chatbots,chatops,devops,automation,opensource)

## Quickstart

```bash
$ pip3 install opsdroid
$ opsdroid start
```

## Documentation

```eval_rst
.. toctree::
   :maxdepth: 2

   overview
   installation
   skills/index
   connectors/index
   databases/index
```

```eval_rst
.. toctree::
   :maxdepth: 2
   :caption: References

   configuration
   cli
   rest-api
```

```eval_rst
.. toctree::
   :maxdepth: 2
   :caption: User guides

   examples/index
   packaging
   testing
```

```eval_rst
.. toctree::
   :maxdepth: 2
   :caption: Project

   contributing
   maintaining/index
   why
```

---

### Contributors

This project exists thanks to all the people who contribute. [[Contribute](https://docs.opsdroid.dev/en/stable/contributing.html#contributing)].
<a href="https://github.com/opsdroid/opsdroid/graphs/contributors"><img src="https://opencollective.com/opsdroid/contributors.svg?width=890" /></a>

## Backers

Thank you to all our backers! 🙏 [[Become a backer](https://opencollective.com/opsdroid#backer)]

<a href="https://opencollective.com/opsdroid#backers" target="_blank"><img src="https://opencollective.com/opsdroid/backers.svg?width=890"></a>

## Sponsors

Support this project by becoming a sponsor. Your logo will show up here with a link to your website. [[Become a sponsor](https://opencollective.com/opsdroid#sponsor)]

<a href="https://opencollective.com/opsdroid/sponsor/0/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/0/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/1/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/1/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/2/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/2/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/3/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/3/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/4/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/4/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/5/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/5/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/6/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/6/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/7/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/7/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/8/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/8/avatar.svg"></a>
<a href="https://opencollective.com/opsdroid/sponsor/9/website" target="_blank"><img src="https://opencollective.com/opsdroid/sponsor/9/avatar.svg"></a>
