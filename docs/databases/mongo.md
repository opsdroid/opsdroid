# opsdroid database mongo

A database module for [opsdroid](https://github.com/opsdroid/opsdroid) to persist memory in a [mongo database](https://www.mongodb.com/).

## Requirements

None.

## Configuration

```yaml
databases:
  - name: mongo
    host:       "my host"     # (optional) default "localhost"
    port:       "12345"       # (optional) default "27017"
    database:   "mydatabase"  # (optional) default "opsdroid"
```
## Performance 

As we develop and operate applications with MongoDB,
 
1. Schema less

2. No complex joins

3. Ease of scale-out

4. Document Oriented Storage

5. Index on any attribute

## Usage
This module helps opsdroid to persist memory using an MongoDB database.
