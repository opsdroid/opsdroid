# PostgreSQL

A database module for [opsdroid](https://github.com/opsdroid/opsdroid) to persist memory in a [postgres database](https://www.postgresql.org/).

## Requirements
An accessible PostgreSQL server with the database that you provide already created.
And `asyncpg` installed for making the requests. Note this package is pre-installed in the docker container.

## Configuration

```yaml
databases:
  postgresql:
    host: "hostname" # (optional) default: "localhost"
    port: 5432 # (optional) default: 5432
    user: "opsdroid" # (optional) default: "opsdroid"
    password: "Please change me"
    database: "opsdroid_db" # (optional) default: "opsdroid"
    table_name: "opsdroid_table" # (optional) default: "opsdroid_default"
```

## Usage
This database connector is unique at the time of writing in it's ability to use different tables to place the key value pairs into. This is optional. Code that doesn't specify a table name will be placed into the table specified in the postgresql database configuration.
```python
await opsdroid.memory.put(key, value, table_name='example_table')
await opsdroid.memory.get(key, table_name='example_table')
```

## Example
Multiple skills sharing the same table can be messy. The following example skill stores data in a table dedicated to the skill.

```yaml
skills:
  pgtestskill:
    table_name: "custom_table_name"
```

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
from opsdroid.events import Message

class pgtestSkill(Skill):
    def __init__(self, *args, **kwargs):
        super(pgtestSkill, self).__init__(*args, **kwargs)
        self.table_name=self.config.get('table_name')

    @match_regex('^!put (?P<key>\w+) (?P<data>\w+)$')
    async def putter(self, message):
        await self.opsdroid.memory.put(
            message.entities['key']['value'],
            message.entities['data']['value'],
            table_name=self.table_name
        )
        await message.respond(
            Message(
                text='ok, stored'
            )
        )

    @match_regex('^!get (?P<key>\w+)$')
    async def getter(self, message):
        data = await self.opsdroid.memory.get(
            message.entities['key']['value'],
            table_name=self.table_name
        )

        await message.respond(
            Message(
                text=str(data)
            )
        )

    @match_regex('^!delete (?P<key>\w+)$')
    async def deleter(self, message):
        data = await self.opsdroid.memory.delete(
            message.entities['key']['value'],
            table_name=self.table_name
        )

        await message.respond(
            Message(
            text="OK! deleted"
            )
        )

    @match_regex('^!list$')
    async def lister(self, message):
        # SELECT * from self.table_name
        pass
```

Using  a [shell](../connectors/shell) connector, the skill returns:
```
opsdroid> !put test1 data1
ok, stored test1
opsdroid> !get test1
data1
opsdroid> !delete test1
OK! deleted test1
opsdroid> !get test1
None
opsdroid> !put test2 data2
ok, stored test2
opsdroid> !put test2 data3
ok, stored test2
opsdroid> !get test2
data3
```
As expected, `psql` shows:
```
opsdroid_db=# select * from custom_table_name;
  key  |  data   
-------+---------
 test2 | "data3"
(1 row)
```
