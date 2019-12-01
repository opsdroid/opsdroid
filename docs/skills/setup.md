# Setup

All initialisation that might be required for your skill can go to the `__init__` method, which takes `opsdroid` and `config` as its arguments.

```python
class MySkill(Skill):
    def __init__(self, opsdroid, config):
        super(MySkill, self).__init__(opsdroid, config)
        # do some setup stuff here
```

**IMPORTANT** Always remember to chain up to the `__init__` method of the `Skill` class, or your skill won’t work!
