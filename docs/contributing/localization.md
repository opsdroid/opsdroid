# Localization
Opsdroid runs by default in English, but it can be translated to your local language. In order to achieve it, [gettext](https://docs.python.org/3/library/gettext.html) and [babel](http://babel.pocoo.org/en/latest/index.html) are used.

To mark a string as translatable, just call the special `_` function:
```python
txt = 'hello {}'.format(name)  # this is NOT translatable
txt = _('hello {}').format(name)  # but now it's translatable! 🎉
```

When some new translatable strings are added, you must extract them to a non-versioned `pot` file with:
```shell
python setup.py extract_messages
```

Then, update all existing language `po` files from the extracted `pot` file with the command:
```shell
python setup.py update_catalog
```

Now, you can translate editing manually or with [Poedit](https://poedit.net/) the `po` files in `locale/<lang>/LC_MESSAGES/opsdroid.po`. Those files contain the real translations and are versioned.

After you made a change in any `po` file, in order to view the changes in opsdroid, you should compile them to `mo` binary files, the format read by python gettext:
```shell
python setup.py compile_catalog
```

## Starting a new language
If your language is not in the `locale` folder, you can initialize it. You will need the [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) code of the language. For example, in order to start a new [Esperanto](https://en.wikipedia.org/wiki/Esperanto) translation:
```shell
python setup.py init_catalog -l eo
```
Then you can translate it in `locale/eo/LC_MESSAGES/opsdroid.po`, then compile it, etc.
