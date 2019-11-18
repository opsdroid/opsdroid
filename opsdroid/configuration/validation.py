"""Schema validation for configuration.yaml."""

from voluptuous import Schema, ALLOW_EXTRA, Optional, Required, Url, Any

logging = {
    "level": str,
    "console": bool,
    "extended": bool,
    "filter": {"whitelist": list, "blacklist": list},
}

parsers = Any(
    None,
    {
        Optional("dialogflow"): {
            Required(
                "project-id",
                msg="Dialogflow parser required param 'project-id' not provided",
            ): str,
            Optional("min-score"): float,
        },
        Optional("luisai"): {
            Required(
                "appid", msg="Luis.ai Parser required param 'appid' not provided"
            ): str,
            Required(
                "appkey", msg="Luis.ai Parser required param 'appkey' not provided"
            ): str,
            Required(
                "verbose", msg="Luis.ai Parser required param 'verbose' not provided"
            ): bool,
            Optional("min-score"): float,
        },
        Optional("sapcai"): {
            Required(
                "token", msg="SAPCAI Parser required param 'token' not provided"
            ): str,
            Optional("min-score"): float,
        },
        Optional("watson"): {
            Required(
                "gateway", msg="Watson Parser required param 'gateway' not provided"
            ): str,
            Required(
                "assistant-id",
                msg="Watson Parser required param 'assistant-id' not provided",
            ): str,
            Required(
                "token", msg="Watson Parser required param 'token' not provided"
            ): str,
            Optional("min-score"): float,
        },
        Optional("witai"): {
            Required(
                "token", msg="Witai Parser required param 'token' not provided"
            ): str,
            Optional("min-score"): float,
        },
        Optional("rasanlu", default=dict): Any(
            None,
            {
                Optional("url"): str,
                Optional("project"): str,
                Optional("token"): str,
                Optional("min-score"): float,
            },
        ),
        Optional("regex", default=dict): Any(None, {Optional("enabled"): bool}),
        Optional("crontab", default=dict): Any(None, {Optional("enabled"): bool}),
        Optional("parse_format", default=dict): Any(None, {Optional("enabled"): bool}),
    },
)

connectors = {
    Optional("websocket"): Any(
        None,
        {
            Optional("bot-name"): str,
            Optional("max-connections"): int,
            Optional("connection-timeout"): int,
        },
    ),
    Optional("ciscospark"): {
        Required(
            "webhook-url",
            msg="CiscoSpark Connector required param 'webhook-url' not provided",
        ): Url,
        Required(
            "token", msg="CiscoSpark Connector required param 'token' not provided"
        ): str,
    },
    Optional("twitter"): {
        Required(
            "consumer_key",
            msg="Twitter Connector required param 'consumer_key' not provided",
        ): str,
        Required(
            "consumer_secret",
            msg="Twitter Connector required param 'consumer_secret' not provided",
        ): str,
        Required(
            "oauth_token",
            msg="Twitter Connector required param 'oath_token' not provided",
        ): str,
        Required(
            "oauth_token_secret",
            msg="Twitter Connector required param 'oath_token_secret' not provided",
        ): str,
        Optional("enable_dms"): bool,
        Optional("enable_tweets"): bool,
    },
    Optional("webexteams"): {
        Required(
            "webhook-url",
            msg="Webexteams Connector required param 'webhook-url' not provided",
        ): Url,
        Required(
            "token", msg="Webexteams Connector required param 'token' not provided"
        ): str,
    },
    Optional("facebook"): {
        Required(
            "verify-token",
            msg="Facebook Connector required param 'verify-token' not provided",
        ): str,
        Required(
            "page-access-token",
            msg="Facebook Connector required param 'page-access-token' not provided",
        ): str,
        Optional("bot-name"): str,
    },
    Optional("matrix"): {
        Required(
            "mxid", msg="Matrix Connector required param 'mxid' not provided"
        ): str,
        Required(
            "password", msg="Matrix Connector required param 'password' not provided"
        ): str,
        Required(
            "rooms", msg="Matrix Connector required param 'rooms' not provided"
        ): dict,
        Optional("homeserver"): str,
        Optional("nick"): str,
        Optional("room_specific_nicks"): bool,
    },
    Optional("mattermost"): {
        Required(
            "token", msg="Mattermost Connector required param 'token' not provided"
        ): str,
        Required(
            "url", msg="Mattermost Connector required param 'url' not provided"
        ): str,
        Required(
            "team-name",
            msg="Mattermost Connector required param 'team-name' not provided",
        ): str,
        Optional("scheme"): str,
        Optional("port"): int,
        Optional("ssl-verify"): bool,
        Optional("connect-timeout"): int,
    },
    Optional("github"): {
        Required(
            "token", msg="Github Connector required param 'token' not provided"
        ): str
    },
    Optional("gitter"): {
        Required(
            "token", msg="Gitter Connector required param 'token' not provided"
        ): str,
        Required(
            "room-id", msg="Gitter Connector required param 'room-id' not provided"
        ): str,
        Optional("bot-name"): str,
    },
    Optional("telegram"): {
        Required(
            "token", msg="Telegram Connector required param 'token' not provided"
        ): str,
        Optional("update-interval"): float,
        Optional("default-user"): str,
        Optional("whitelisted-users"): list,
    },
    Optional("slack"): {
        Required(
            "token", msg="Slack Connector required param 'token' not provided"
        ): str,
        Optional("bot-name"): str,
        Optional("default-room"): str,
        Optional("icon-emoji"): str,
        Optional("connect-timeout"): int,
        Optional("chat-as-user"): bool,
    },
    Optional("rocketchat"): {
        Required(
            "token", msg="Rocket.chat Connector required param 'token' not provided"
        ): str,
        Required(
            "user-id", msg="Rocket.chat Connector required param 'user-id' not provided"
        ): str,
        Optional("bot-name"): str,
        Optional("default-room"): str,
        Optional("channel-url"): Url,
        Optional("update-interval"): int,
        Optional("group"): str,
    },
    Optional("shell"): Any(None, {Optional("bot-name"): str}),
}

databases = Any(
    None,
    {
        Optional("redis"): Any(
            None,
            {
                Optional("host"): str,
                Optional("port"): Any(int, str),
                Optional("database"): int,
                Optional("password"): str,
            },
        ),
        Optional("mongo"): Any(
            None,
            {
                Optional("host"): str,
                Optional("port"): Any(int, str),
                Optional("database"): str,
            },
        ),
        Optional("sqlite"): Any(None, {Optional("file"): str, Optional("table"): str}),
    },
)

schema = {
    "logging": logging,
    "module-path": str,
    "welcome-message": bool,
    "web": {"host": str, "port": int, "ssl": {"cert": str, "key": str}},
    "parsers": parsers,
    "connectors": connectors,
    "databases": databases,
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
