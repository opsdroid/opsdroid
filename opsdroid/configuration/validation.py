

# Import Yamale and make a schema object, make sure ruamel.yaml is installed already.
import yamale
schema = yamale.make_schema('shema.yaml')

# Create a Data object
data = yamale.make_data('example1_configuration.yaml')

# Validate data against the schema same as before.
yamale.validate(schema, data)

