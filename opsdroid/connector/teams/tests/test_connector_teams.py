from opsdroid.connector.teams import TeamsConnector


def test_teams_init():
    connector = TeamsConnector({})
    assert connector.name == "teams"
