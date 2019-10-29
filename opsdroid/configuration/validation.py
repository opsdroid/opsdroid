"""Schema validation for configuration.yaml."""

from voluptuous import Schema, ALLOW_EXTRA


schema = {
    "logging": {"level": str, "console": bool},
    "welcome-message": bool,
    "connectors": [{"name": str, "token": str, "access-token": str}],
    "skills": [{"name": str}],
}


def validate_configuration(data):
    """Validate data from configuration.yaml.

    We use voluptuous to validate the data obtained from the
    configuration file with the schema declared above. Voluptuous
    will raise a 'voluptuous.MultipleInvalid' exception if the data
    passed doesn't match the schema.

    This is a helper function so we don't need to do much with it other than
    initialize voluptuous.Schema and attempt to validate the data. The function
    'load_config_file' located on 'opsdroid.configuration.__init__' will handle
    the case when the exception is raised.

    Args:
        data: a yaml stream obtained from opening configuration.yaml
    """

    validate = Schema(schema, extra=ALLOW_EXTRA)

    validate(data)
