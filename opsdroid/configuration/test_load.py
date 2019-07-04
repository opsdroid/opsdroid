import os
import unittest.mock as mock

from yamale import yamale

from opsdroid import loader as ld
from opsdroid.__main__ import configure_lang
from opsdroid.loader import Loader







configure_lang({})
opsdroid = mock.MagicMock()
loader = ld.Loader(opsdroid)

config = loader.load_config_file(
    [os.path.abspath("./example_1.yaml")],("./schema.yaml")
)

print(config)



# schema = yamale.make_schema(os.path.normpath("/opsdroid/configuration/schema.yaml"))
# # schema = yamale.make_schema(os.path.abspath("opsdroid/configuration/schema.yaml"))
#
# # schema = yamale.make_schema(os.path.normpath('./schema.yaml'))
#
# # data = yamale.make_data('.opsdroid/configuration/example_configuration.yaml')
# data = yamale.make_data('./example_configuration.yaml')
#
# yamale.validate(schema, data)
# /home/olga/projects/news/opsdroid/opsdroid/configuration/opsdroid/configuration/schema.yaml