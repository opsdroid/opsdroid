# Module packaging

Opsdroid can be extended by developing a new skill, connector, or database extensions.

## Single-module extensions

An extension can be something as simple as a small python module placed in your local path, or somewhere in `PYTHONPATH`.
An extension module can also be put in a GitHub repository from which it can be automatically retrieved by opsdroid. Here are
some examples on how to configure opsdroid to find extension modules, in this case, skills:

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
    repo: https://github.com/me/mygithubskill.git

  ## From PYTHONPATH
  - name: myimportedskill
    module: 'my.imported.skill'

  ## Hello world (https://github.com/opsdroid/skill-hello)
  - name: hello
```

Details on pointing opsdroid to extension modules can be found in the [configuration reference](configuration.md).
For more on creating skills, see the [next section](skills/index.md) of these docs.

## Packaged Python extensions

Larger extensions packaged as regular Python packages can be used simply by installing them as any other Python packages,
from e.g. PyPI.

Opsdroid will dynamically discover installed extension packages and use them if it sees their names in the `configuration.yaml`
configuration file. There is **no additional lookup configuration required**: the extension name is enough.

To be dynamically discoverable, Opsdroid extensions developed and deployed as regular Python packages must define so-called
[entry points](https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins),
one for each opsdroid extension.

The entry points are grouped by extension type (skill, connector or database). The groups are called `opsdroid_skills`,
`opsdroid_connectors` and `opsdroid_databases`.

Defining entry points for opsdroid is as simple as adding a small dict entry to the `setup.py` file of the extension
package. For example:

```python
 entry_points = {
     'opsdroid_databases': [
         'zodb = opsdroid_zodb.database'
      ]
 },
```

(an excerpt from `setup.py` file of the [opsdroid-zodb](https://github.com/koodaamo/opsdroid-zodb) extension package)

In the above example, `entry_points` is just yet another named keyword argument to the `setup()` call found in `setup.py`.
It defines an opsdroid [ZODB](http://www.zodb.org) database extension whose name is 'zodb'. It then declares that opsdroid
should import the extension from the `database` module of an `opsdroid_zodb` package.

An extension package with the above entry point could be used from `configuration.yaml` simply thus:

```yaml
databases:
  ## From an installed Python package
  zodb: {}
```

That's all! Opsdroid will see the `zodb` extension name, check it against all `opsdroid_databases` entry points it is aware of,
import the extension and use it.

The above entry point example defines just one database extension. To add more database extensions, or also skill(s) or
connector(s), simply add them to the same dict data structure, following the extension group naming convention given above.
