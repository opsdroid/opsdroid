"""Tests for the ConnectorMatrix class."""
import asyncio
import aiohttp

import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock
from matrix_api_async import AsyncHTTPAPI
from matrix_client.errors import MatrixRequestError

from opsdroid.core import OpsDroid
from opsdroid.connector.matrix import ConnectorMatrix
from opsdroid.message import Message
from opsdroid.__main__ import configure_lang

api_string = 'matrix_api_async.AsyncHTTPAPI.{}'

def setup_connector():
    connector = ConnectorMatrix(
        {"room": "#test:localhost",
         "mxid": "@opsdroid:localhost",
         "password": "hello",
         "homeserver": "http://localhost:8008"}
    )
    return connector


class TestConnectorMatrixAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Matrix connector class."""
    @property
    def sync_return(self):
        return {
            "account_data": {
                "events": []
            },
            "device_lists": {
                "changed": [],
                "left": []
            },
            "device_one_time_keys_count": {
                "signed_curve25519": 50
            },
            "groups": {
                "invite": {},
                "join": {},
                "leave": {}
            },
            "next_batch": "s801873745",
            "presence": {
                "events": []
            },
            "rooms": {
                "invite": {},
                "join": {
                    "!aroomid:localhost": {
                        "account_data": {
                            "events": []
                        },
                        "ephemeral": {
                            "events": []
                        },
                        "state": {
                            "events": []
                        },
                        "summary": {},
                        "timeline": {
                            "events": [
                                {
                                    "content": {
                                        "body": "LOUD NOISES",
                                        "msgtype": "m.text"
                                    },
                                    "event_id": "$eventid:localhost",
                                    "origin_server_ts": 1547124373956,
                                    "sender": "@cadair:cadair.com",
                                    "type": "m.room.message",
                                    "unsigned": {
                                        "age": 3498
                                    }
                                }
                            ],
                            "limited": False,
                            "prev_batch": "s801873709_690923311_714269_220789851_103743426_545343_16236676_11101067_27940"
                        },
                        "unread_notifications": {
                            "highlight_count": 0,
                            "notification_count": 0
                        }
                    }
                },
                "leave": {}
            },
            "to_device": {
                "events": []
            }
        }

    def setUp(self):
        self.connector = setup_connector()
        self.api = AsyncHTTPAPI('https://notaurl.com', None)
        self.connector.connection = self.api

    async def test_make_filter(self):
        with amock.patch(api_string.format('create_filter')) as patched_filter:
            patched_filter.return_value = asyncio.Future()
            patched_filter.return_value.set_result({'filter_id': 'arbitrary string'})
            test_rooms = ['!notaroom:matrix.org', '!notanotherroom:matrix.org']
            filter_id = await self.connector.make_filter(self.api, test_rooms)
            assert filter_id == 'arbitrary string'

            assert patched_filter.called
            assert patched_filter.call_args[1]['user_id'] == '@opsdroid:localhost'
            assert patched_filter.call_args[1]['filter_params']['room']['rooms'] == test_rooms

    async def test_connect(self):
        with amock.patch(api_string.format('login')) as patched_login, \
             amock.patch(api_string.format('join_room')) as patched_join_room, \
             amock.patch(api_string.format('create_filter')) as patched_filter, \
             amock.patch(api_string.format('sync')) as patched_sync, \
             OpsDroid() as opsdroid:

            patched_login.return_value = asyncio.Future()
            patched_login.return_value.set_result({'access_token': 'arbitrary string1'})

            patched_join_room.return_value = asyncio.Future()
            patched_join_room.return_value.set_result({'room_id': '!aroomid:localhost'})

            patched_filter.return_value = asyncio.Future()
            patched_filter.return_value.set_result({'filter_id': 'arbitrary string'})

            patched_sync.return_value = asyncio.Future()
            patched_sync.return_value.set_result({'next_batch': 'arbitrary string2'})

            await self.connector.connect()

            assert '!aroomid:localhost' in self.connector.room_ids.values()

            assert self.connector.connection.token == 'arbitrary string1'

            assert self.connector.filter_id == 'arbitrary string'

            assert self.connector.connection.sync_token == 'arbitrary string2'

    async def test_listen(self):
        self.connector.room_ids = {'main': '!aroomid:localhost'}
        self.connector.filter_id = 'arbitrary string'

        with amock.patch(api_string.format('get_display_name')) as patched_name:
            patched_name.return_value = asyncio.Future()
            patched_name.return_value.set_result('SomeUsersName')

            returned_message = await self.connector._parse_sync_response(self.sync_return)

            assert returned_message.text == 'LOUD NOISES'
            assert returned_message.user == 'SomeUsersName'
            assert returned_message.room == '!aroomid:localhost'
            assert returned_message.connector == self.connector
            raw_message = self.sync_return['rooms']['join']['!aroomid:localhost']['timeline']['events'][0]
            assert returned_message.raw_message == raw_message

    async def test_get_nick(self):
        self.connector.room_specific_nicks = True

        with amock.patch(api_string.format('get_room_displayname')) as patched_roomname, \
             amock.patch(api_string.format('get_display_name')) as patched_globname:
            patched_roomname.return_value = asyncio.Future()
            patched_roomname.return_value.set_result('')

            mxid = '@notaperson:matrix.org'
            assert await self.connector._get_nick('!notaroom:matrix.org', mxid) == ''
            # Test if a room displayname couldn't be found
            patched_roomname.side_effect = Exception()

            # Test if that leads to a global displayname being returned
            patched_globname.return_value = asyncio.Future()
            patched_globname.return_value.set_result('@notaperson')
            assert await self.connector._get_nick('!notaroom:matrix.org', mxid) == '@notaperson'

            # Test that failed nickname lookup returns the mxid
            patched_globname.side_effect = MatrixRequestError()
            assert await self.connector._get_nick('!notaroom:matrix.org', mxid) == mxid

    async def test_get_html_content(self):
        original_html = "<p><h3><no>Hello World</no></h3></p>"
        original_body = "### Hello World"
        message = await self.connector._get_html_content(original_html)
        assert message['formatted_body'] == "<h3>Hello World</h3>"
        assert message['body'] == "Hello World"

        message = await self.connector._get_html_content(original_html,
                                                         original_body)
        assert message['formatted_body'] == "<h3>Hello World</h3>"
        assert message['body'] == "### Hello World"

    # async def test_respond(self):
    #     message = await self.connector._parse_sync_response(self.sync_return)

    #     self.connector.respond(message)

    async def test_disconnect(self):
        self.connector.session = amock.MagicMock()
        self.connector.session.close = amock.CoroutineMock()
        await self.connector.disconnect()
        assert self.connector.session.close.called

    async def get_roomname(self):
        pass
