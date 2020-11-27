## Documentation
More documentation is always appreciated and it's something that you can contribute to from the GitHub web interface.  This might be a great start point if you are new to Open Source and GitHub!

Things that we need help with:

 - More documentation. Something that you think is unclear?
 - More examples of how to use opsdroid
 - More Tutorials
 - Typos/Grammar check
 - Blog posts, articles, etc
 - Any issue marked with the [documentation tag](https://github.com/opsdroid/opsdroid/issues?q=is:issue+is:open+label:documentation)

### Building the docs

Opsdroid's documentation is built using [Sphinx](http://www.sphinx-doc.org/en/master/) with the [Recommonmark](https://github.com/readthedocs/recommonmark) and [Napoleon](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html) plugins and is hosted on [readthedocs](https://readthedocs.org/).

You can build the documentation yourself locally and view them using the built in Python web server.

```console
$ tox -e docs  # or `sphinx-build -b html docs/ docs/_build/`
The HTML pages are in docs\_build.

$ cd docs/_build && python -m http.server
Serving HTTP on 0.0.0.0 port 8000 (http://localhost:8000/) ...
```

### Writing documentation

All documentation should be written in [Basic English](https://en.wikipedia.org/wiki/Basic_English) where possible. We should try to keep words, phrases and grammar as simple as possible to make the project as accessible as possible.

[Markdown](https://en.wikipedia.org/wiki/Markdown) is our preferred markup language, although [reStructuredText](http://docutils.sourceforge.net/rst.html) (rst) is also supported. You may also embed portions of rst within your markdown documentation with the following syntax:

~~~
```eval_rst
.. warning::
   This is a warning admonition from rst within a markdown document.
   Useful because markdown doesn't have warnings.
```
~~~

Renders as:


```eval_rst
.. warning::
   This is a warning admonition from rst within a markdown document.
   Useful because markdown doesn't have warnings.
```

You can also use [Sphinx autodoc directives](http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) to embed docstrings from the opsdroid module within your markdown documentation too.

~~~
```eval_rst
.. autofunction:: opsdroid.matchers.match_event
```
~~~

Renders as:

```eval_rst
.. autofunction:: opsdroid.matchers.match_event
   :noindex:
```

It is preferable to keep as much documentation within docstrings in the opsdroid codebase as possible and to include it in the documentation website using autodoc.
