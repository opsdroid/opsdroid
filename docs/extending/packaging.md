# Extension packaging

To be dynamically discoverable, Opsdroid extensions developed and deployed as regular Python packages must define so-called 
[entry points](https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins),
one for each individual opsdroid extension.

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
It defines a opsdroid [ZODB](http://www.zodb.org) database extension whose name is 'zodb'. It then declares that opsdroid
should import the extension from the `database` module of a `opsdroid_zodb` package.

An extension package with the above entry point could be used from `configuration.yaml` simply thus:

```yaml
databases:
  ## From a installed Python package
  - name: zodb
```

That's all! Opsdroid will see the `zodb` extension name, check it against all `opsdroid_databases` entry points it is aware of,
import the extension and use it.

The above entry point example defines just one database extension. To add more database extensions, or also skill(s) or
connector(s), simply add them to the same dict data structure, following the extension group naming convention given above.
