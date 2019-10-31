"""Schema validation for configuration.yaml."""

from voluptuous import Schema, ALLOW_EXTRA, Optional, Required, Url

# parsers_config = {
#     "name": str,
#     "enabled": bool,
#     "token": str,
#     "appid": str,
#     "appkey": str,
#     "verbose": bool,
#     "min-score": float,
# }

parsers_config = {
    "name": str,
    "enabled": bool,
    "token": str,
    "appid": str,
    "appkey": str,
    "verbose": bool,
    "min-score": float,
}

connectors_config = {
    "name": str,
    "bot-name": str,
    "max-connections": int,
    "connection-timeout": int,
    "webhook-url": Url(),
    "consumer-key": str,
    "consumer-secret": str,
    "oauth-token": str,
    "oauth-token-secret": str,
    "enable_dms": str,
    "verify-token": str,
    "page-access-token": str,
    "mxid": str,
    "password": str,
    "room": str,
    "rooms": dict,
    "homeserver": str,
    "nick": str,
    "room_specific_nicks": str,
    "token": str,
    "update-interval": int,
    "default-user": str,
    "whitelisted-users": list,
    "default-room": str,
    "icon-emoji": str,
    "connection-timeout": int,
    "user-id": str,
    "group": str,
    "channel-url": Url(),
}


# schema = {
#     "logging": {"level": str, "console": bool},
#     "welcome-message": bool,
#     "connectors": [{"name": str, "token": str}],
#     "skills": [{"name": str}],
#     Optional("parsers", default=list): [parsers_config],
#     Required("connectors", default=list): [connectors_config],
#     # Optional("databases", default=list): [
#     #     {
#     #         "name": str,
#     #         "host": str,
#     #         "port": str,
#     #         Optional("database", default=int): str,
#     #         "password": str,
#     #         "reconnect": bool,
#     #         "file": str,
#     #         "table": str,
#     #     }
#     # ],
#     Optional("skills", default=list): [{"name": str}],
# }

schema = {
    "logging": {"level": str, "console": bool},
    "welcome-message": bool,
    "connectors": [{"name": str, "token": str, "access-token": str}],
    "skills": [{"name": str}],
    Optional("parsers", default=list): {
        Optional("watson"): {
            Required("gateway", msg="Watson Parser required param not provided"): str,
            Required(
                "assistant-id", msg="Watson Parser required param not provided"
            ): str,
            Required("token", msg="Watson Parser required param not provided"): str,
        },
        Optional("regex"): {
            Required("enabled", msg="Regex Parser required param not provided"): bool
        },
    },
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
    print(data)
    print(type(data["parsers"]["regex"]))
    validate = Schema(schema, extra=ALLOW_EXTRA)
    print(validate)
    validate(data)
