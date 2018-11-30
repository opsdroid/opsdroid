# Opsdroid extensions

Opsdroid can be extended by developing new skill, connector, or database extensions.

## Single-module extensions

An extension can be something as simple as a small python module placed in your local path, or somewhere in PYTHONPATH.
An extension module can also be put in a GitHub repository from which it can be automatically retrieved by opsdroid. Here are
some examples on how to configure opsdroid to find extension modules, in this case skills:

```yaml
skills:
  ## From local folder
  - name: myawesomeskill
    path: /home/me/src/opsdroid-skills/myawesomeskill
  ## From local file
  - name: mysimpleskill
    path: /home/me/src/opsdroid-skills/mysimpleskill.py
  ## From custom repository
  - name: mygithubskill
    path: https://github.com/me/mygithubskill.git
  ## From PYTHONPATH
  - name: myimportedskill
    module: 'my.imported.skill'
  ## Hello world (https://github.com/opsdroid/skill-hello)
  - name: hello
```

Details on pointing opsdroid to extension modules can be found in the [configuration reference](../configuration-reference.md).
For more on creating skills, see the [next section](./skills.md) of these docs.

## Packaged extensions

Larger extensions packaged as regular Python packages can be used simply by installing them as any other Python packages,
from e.g. PyPI.

Opsdroid will dynamically discover installed extension packages and use them if it sees their names in the `configuration.yaml`
configuration file. There is **no additional lookup configuration required**: the extension name is enough.

For dynamic discovery to work, packaged extensions must define so-called entry points in their setup. See the docs on
[extension packaging](./packaging.md) for detailed instructions and examples that make it easy to create dynamically
discoverable extensions.
