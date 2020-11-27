import asyncio

import asynctest
import asynctest.mock as amock

from opsdroid import events
from opsdroid.core import OpsDroid
from opsdroid.connector import Connector
from opsdroid.cli.start import configure_lang


class TestEventCreator(asynctest.TestCase):
    """Test the opsdroid event creation class"""

    async def setup(self):
        pass

    async def test_create_event(self):
        creator = events.EventCreator(Connector({}))

        self.assertEqual(None, await creator.create_event({"type": "NotAnEvent"}, ""))


class TestEvent(asynctest.TestCase):
    """Test the opsdroid event class."""

    async def setup(self):
        configure_lang({})

    async def test_event(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.Event("user_id", "user", "default", mock_connector)

        self.assertEqual(event.user_id, "user_id")
        self.assertEqual(event.user, "user")
        self.assertEqual(event.target, "default")

    async def test_entities(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.Event("user_id", "user", "default", mock_connector)

        event.update_entity("city", "London", 0.8)
        assert event.entities["city"]["value"] == "London"
        assert event.entities["city"]["confidence"] == 0.8
        assert event.get_entity("city") == "London"

    def test_unique_subclasses(self):
        with self.assertRaises(NameError):

            class Message(events.Event):
                pass

        class Message(events.Event):  # noqa
            _no_register = True
            pass


class TestMessage(asynctest.TestCase):
    """Test the opsdroid message class."""

    async def setup(self):
        configure_lang({})

    async def test_message(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector({}, opsdroid=opsdroid)
            raw_message = {
                "text": "Hello world",
                "user_id": "user_id",
                "user": "user",
                "room": "default",
                "timestamp": "01/01/2000 19:23:00",
                "messageId": "101",
            }
            message = events.Message(
                text="Hello world",
                user_id="user_id",
                user="user",
                target="default",
                connector=mock_connector,
                raw_event=raw_message,
            )

            self.assertEqual(message.text, "Hello world")
            self.assertEqual(message.user_id, "user_id")
            self.assertEqual(message.user, "user")
            self.assertEqual(message.target, "default")
            self.assertEqual(message.raw_event["timestamp"], "01/01/2000 19:23:00")
            self.assertEqual(message.raw_event["messageId"], "101")
            with self.assertRaises(TypeError):
                await message.respond("Goodbye world")
            # Also try responding with just some empty Event
            with self.assertRaises(TypeError):
                await message.respond(
                    events.Event(message.user, message.target, message.connector)
                )

    async def test_response_effects(self):
        """Responding to a message shouldn't change the message."""
        with OpsDroid() as opsdroid:
            mock_connector = Connector({}, opsdroid=opsdroid)
            message_text = "Hello world"
            message = events.Message(
                message_text, "user_id", "user", "default", mock_connector
            )
            with self.assertRaises(TypeError):
                await message.respond("Goodbye world")
            self.assertEqual(message_text, message.text)

    async def test_thinking_delay(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector(
                {
                    "name": "shell",
                    "thinking-delay": 3,
                    "type": "connector",
                    "module_path": "opsdroid-modules.connector.shell",
                },
                opsdroid=opsdroid,
            )

            with amock.patch("opsdroid.events.Message._thinking_delay") as logmock:
                message = events.Message(
                    "hi", "user_id", "user", "default", mock_connector
                )
                with self.assertRaises(TypeError):
                    await message.respond("Hello there")

                self.assertTrue(logmock.called)

    async def test_thinking_sleep(self):
        with OpsDroid() as opsdroid:
            mock_connector_int = Connector(
                {
                    "name": "shell",
                    "thinking-delay": 3,
                    "type": "connector",
                    "module_path": "opsdroid-modules.connector.shell",
                },
                opsdroid=opsdroid,
            )

            with amock.patch("asyncio.sleep") as mocksleep_int:
                message = events.Message(
                    "hi", "user_id", "user", "default", mock_connector_int
                )
                with self.assertRaises(TypeError):
                    await message.respond("Hello there")

                self.assertTrue(mocksleep_int.called)

            # Test thinking-delay with a list

            mock_connector_list = Connector(
                {
                    "name": "shell",
                    "thinking-delay": [1, 4],
                    "type": "connector",
                    "module_path": "opsdroid-modules.connector.shell",
                },
                opsdroid=opsdroid,
            )

            with amock.patch("asyncio.sleep") as mocksleep_list:
                message = events.Message(
                    "hi", "user_id", "user", "default", mock_connector_list
                )
                with self.assertRaises(TypeError):
                    await message.respond("Hello there")

                self.assertTrue(mocksleep_list.called)

    async def test_typing_delay(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector(
                {
                    "name": "shell",
                    "typing-delay": 0.3,
                    "type": "connector",
                    "module_path": "opsdroid-modules.connector.shell",
                },
                opsdroid=opsdroid,
            )
            with amock.patch("opsdroid.events.Message._typing_delay") as logmock:
                with amock.patch("asyncio.sleep") as mocksleep:
                    message = events.Message(
                        "hi", "user_id", "user", "default", mock_connector
                    )
                    with self.assertRaises(TypeError):
                        await message.respond("Hello there")

                    self.assertTrue(logmock.called)
                    self.assertTrue(mocksleep.called)

            # Test thinking-delay with a list

            mock_connector_list = Connector(
                {
                    "name": "shell",
                    "typing-delay": [1, 4],
                    "type": "connector",
                    "module_path": "opsdroid-modules.connector.shell",
                },
                opsdroid=opsdroid,
            )

            with amock.patch("asyncio.sleep") as mocksleep_list:
                message = events.Message(
                    "hi", "user_id", "user", "default", mock_connector_list
                )
                with self.assertRaises(TypeError):
                    await message.respond("Hello there")

                self.assertTrue(mocksleep_list.called)

    async def test_typing_sleep(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector(
                {
                    "name": "shell",
                    "typing-delay": 6,
                    "type": "connector",
                    "module_path": "opsdroid-modules.connector.shell",
                },
                opsdroid=opsdroid,
            )
            with amock.patch("asyncio.sleep") as mocksleep:
                message = events.Message(
                    "hi", "user_id", "user", "default", mock_connector
                )
                with self.assertRaises(TypeError):
                    await message.respond("Hello there")

                self.assertTrue(mocksleep.called)

    async def test_react(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector(
                {"name": "shell", "thinking-delay": 2, "type": "connector"},
                opsdroid=opsdroid,
            )
            with amock.patch("asyncio.sleep") as mocksleep:
                message = events.Message(
                    "Hello world", "user_id", "user", "default", mock_connector
                )
                with self.assertRaises(TypeError):
                    await message.respond(events.Reaction("emoji"))
                self.assertTrue(mocksleep.called)


class TestFile(asynctest.TestCase):
    """Test the opsdroid file class"""

    async def setup(self):
        configure_lang({})

    async def test_file(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.File(
            bytes("some file contents", "utf-8"),
            user_id="user_id",
            user="user",
            target="default",
            connector=mock_connector,
        )

        self.assertEqual(event.user_id, "user_id")
        self.assertEqual(event.user, "user")
        self.assertEqual(event.target, "default")
        self.assertEqual((await event.get_file_bytes()).decode(), "some file contents")

    def test_error_on_construct(self):
        with self.assertRaises(ValueError):
            events.File()

        with self.assertRaises(ValueError):
            events.File(b"a", "https://localhost")

    @amock.patch("aiohttp.ClientSession.get")
    async def test_repeat_file_bytes(self, mock_get):
        f = events.File(url="http://spam.eggs/monty.jpg")

        fut = asyncio.Future()
        fut.set_result(b"bob")

        mock_get.return_value.__aenter__.return_value.read = amock.CoroutineMock(
            return_value=fut
        )

        assert await f.get_file_bytes() == b"bob"
        assert mock_get.call_count == 1

        # Now test we don't re-download the url
        assert await f.get_file_bytes() == b"bob"
        assert mock_get.call_count == 1


class TestImage(asynctest.TestCase):
    """Test the opsdroid image class"""

    gif_bytes = (
        b"GIF89a\x01\x00\x01\x00\x00\xff\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
    )

    async def setup(self):
        configure_lang({})

    async def test_image(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.Image(
            self.gif_bytes,
            user_id="user_id",
            user="user",
            target="default",
            connector=mock_connector,
        )

        self.assertEqual(event.user_id, "user_id")
        self.assertEqual(event.user, "user")
        self.assertEqual(event.target, "default")
        self.assertEqual(await event.get_file_bytes(), self.gif_bytes)
        self.assertEqual(await event.get_mimetype(), "image/gif")
        self.assertEqual(await event.get_dimensions(), (1, 1))

    async def test_explicit_mime_type(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.Image(
            self.gif_bytes,
            user_id="user_id",
            user="user",
            target="default",
            mimetype="image/jpeg",
            connector=mock_connector,
        )

        self.assertEqual(await event.get_mimetype(), "image/jpeg")

    async def test_no_mime_type(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.Image(
            b"aslkdjsalkdjlaj",
            user_id="user_id",
            user="user",
            target="default",
            connector=mock_connector,
        )

        self.assertEqual(await event.get_mimetype(), "")


class TestVideo(asynctest.TestCase):
    """Test the opsdroid Video class"""

    mkv_bytes = b'\x1aE\xdf\xa3\xa3B\x86\x81\x01B\xf7\x81\x01B\xf2\x81\x04B\xf3\x81\x08B\x82\x88matroskaB\x87\x81\x04B\x85\x81\x02\x18S\x80g\x01\x00\x00\x00\x00\x00\x08S\x11M\x9bt\xc1\xbf\x84f\xe0E\xc7M\xbb\x8bS\xab\x84\x15I\xa9fS\xac\x81\xe5M\xbb\x8cS\xab\x84\x16T\xaekS\xac\x82\x01UM\xbb\x8cS\xab\x84\x12T\xc3gS\xac\x82\x01\xe2M\xbb\x8cS\xab\x84\x1cS\xbbkS\xac\x82\x087\xec\x01\x00\x00\x00\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x15I\xa9f\xeb\xbf\x84\x10N\x0e,*\xd7\xb1\x83\x0fB@{\xa9\x85videoM\x80\x8dLavf58.29.100WA\x9aHandBrake 1.3.3 2020061500s\xa4\x90\x9b\xf1\x82\xac\x9a\xfa\n\xbch\xc2\rSf\t8"Da\x88\x08\xb7\x80\x95\xd1\xcf\x9c\x00D\x89\x88@\x8f@\x00\x00\x00\x00\x00\x16T\xaek@\x87\xbf\x84\xb3\xf6V5\xae\x01\x00\x00\x00\x00\x00\x00x\xd7\x81\x01s\xc5\x81\x01\x9c\x81\x00"\xb5\x9c\x83und\x86\x8fV_MPEG4/ISO/AVC\x83\x81\x01#\xe3\x83\x84\x0b\xeb\xc2\x00\xe0\x01\x00\x00\x00\x00\x00\x00\x12\xb0\x81 \xba\x81 T\xb0\x81\x10T\xba\x81\tT\xb2\x81\x03c\xa2\xad\x01M@\x1f\xff\xe1\x00\x1egM@\x1f\xec\xa4\xb7\xfe\x00 \x00\x12\xd4\x18\x18\x19\x00\x00\x03\x00\x01\x00\x00\x03\x00\n\x8f\x181\x96\x01\x00\x04h\xce\x04\xf2\x12T\xc3g@\x82\xbf\x84V\x8d\xc4\xbess\x01\x00\x00\x00\x00\x00\x00.c\xc0\x01\x00\x00\x00\x00\x00\x00\x00g\xc8\x01\x00\x00\x00\x00\x00\x00\x1aE\xa3\x87ENCODERD\x87\x8dLavf58.29.100ss\x01\x00\x00\x00\x00\x00\x00:c\xc0\x01\x00\x00\x00\x00\x00\x00\x04c\xc5\x81\x01g\xc8\x01\x00\x00\x00\x00\x00\x00"E\xa3\x88DURATIOND\x87\x9400:00:01.000000000\x00\x00\x1fC\xb6uE\xc7\xbf\x84J\xfd>P\xe7\x81\x00\xa3Do\x81\x00\x00\x80\x00\x00\x02\xf1\x06\x05\xff\xff\xed\xdcE\xe9\xbd\xe6\xd9H\xb7\x96,\xd8 \xd9#\xee\xefx264 - core 155 r2917 0a84d98 - H.264/MPEG-4 AVC codec - Copyleft 2003-2018 - http://www.videolan.org/x264.html - options: cabac=0 ref=1 deblock=0:0:0 analyse=0x1:0x111 me=hex subme=2 psy=1 psy_rd=1.00:0.00 mixed_ref=0 me_range=16 chroma_me=1 trellis=0 8x8dct=0 cqm=0 deadzone=21,11 fast_pskip=1 chroma_qp_offset=0 threads=1 lookahead_threads=1 sliced_threads=0 nr=0 decimate=1 interlaced=0 bluray_compat=0 constrained_intra=0 bframes=3 b_pyramid=2 b_adapt=1 b_bias=0 direct=1 weightb=0 open_gop=0 weightp=0 keyint=50 keyint_min=5 scenecut=40 intra_refresh=0 rc_lookahead=10 rc=crf mbtree=1 crf=22.0 qcomp=0.60 qpmin=0 qpmax=69 qpstep=4 vbv_maxrate=14000 vbv_bufsize=14000 crf_max=0.0 nal_hrd=none filler=0 ip_ratio=1.40 aq=1:1.00\x00\x80\x00\x00\x01re\x88\x84\x02\xb1\x08\x8d\t\xd8p~\x16\x00\x01\x03%\x1e\x1f\xd4\x98T\x98\x05\x7f\x00y\x88\x02`\x00\x10\x01\xb0\x16"\x1dY\x80\x1a\x99\x18\x18%<K@5\xac}F\xaa\xea\x1b[}\xfd\xb0\xc2\xa0\xb0\xc0\x05\x01\xa9\x83\xfe\x14|b\xfd\x9b\x06\n\xe0;\xde\x12\xf5\x06\x8e\x0f\xc2_\xe4\xc2\xa0-\xd0\n\xd2\x02\xc7\xb7\xc8i@\x92@0\r\x0et\x00\xd2\x0e\xcc=\xc1\x99\x1dg8\xd2\x04\xb7\x91\x83K\x8f\xfc\xe7:\xc8\xd2\x08\xa5\x0cw\xd5\x9d\xb1\xaa\xc7\xd7t\xc9\xeb5w\x19\x8e\xdae\x8cH\x82\x11\x05\x99\x10{x_\x0f\xac%\x03k\x94D\xaa\xe2\xf0\xa1\xbb\xb0\\\x93\x81M\xecww\xa7\x84\xf0\xc6Ik\xfe3U\xcc\x02\xff\xff\x06<\x8c\x82\xe9\xa1\xb4o\xc4\xf8\x15\xce\xda\xef\x06\xf0\n\xc4\xb0\xfcb?\xaf\xf3\xf2\xa0}.\xfc}\x16g\x92[6\xaf\xe0\x13\xfc#m\xac\xaa+\x87\xffT;\xbf\xf1lrLO_C\xf7\xe5\x1e\xcdM\x98\x04\xbf\xb7\xf2.\xb2\x87\x8e\xbb$j\x1fyp\xf9\x80\x94\x82\x08%)K\x1bj\x02&|\x9d|\xb9v\xd1a\xad\xfe\x00+\xcdag\xb1\xe2r\x86<u\xa8I\xb6\xab6\xc0\xa4\x91YA\xec\x9f\x8a\x80|\xcb\xdb|\x01\xb1\xe8]\x88\x88\xb9\x8d\xc0\xfc^m}\xf7f\x9a\xb8K\xda\xd0a\xbc\xa2\xb8\x90^P\xdb\xaa\xca]\x0f\xe0\x05\xf6\xc6\x11I<\x8b\xcf`\rZzy\xf8$y\xae\xc8\xfb\\\xfe0\x8f7\xfc\xa3@\x9d\x81\x02X\x00\x00\x00\x00\x95A\x9a#\x03,\x91|\x0c3\x18\xcd\xcbf\x17\x96z\x8bw\x08\\\x1c\xea!\x03\x92\x88\xc5\xe4\x80m|E\xadMw0\xb2\xfa#\x88\x12&4\xb0\x14\xd9\x8e\x8e\x1e\x8e\x91\x87\xf3\x1aS\xe2\x7f\xba\xd3,\r7j\xdd\xf8\x95q\x9a\x0cUm\x987\x01\x82+l\xbd\xa3\x03>\xef\x18i\xd1\x99\x81d\x84\xd4=r\xb0\xf6\x81\x99\x85;\x87xcN\xaa\x92\xa9\xa3x%oO\x02\xa9-\x8b\xc9~V\x1b\x84\xe2\x02\x84\xcc h\xea*xD\x1c\xbf\x17\xc7\xa9\xf5f1\x10\xe7\xf6\x97\x86\x19+k\x99\xac\xf2`\xa3\xd4\x81\x00\xc8\x00\x00\x00\x00LA\x9eA@\xcb7p\x8e\xceIn\x11\x99FF"\x1c\x035\xbf\xc3z\xfb\x91\x8a*\x10p\x9d\x95\xb4\x14\x8a\xca\xc3\xa9\xca\xce\xa4\xb5\xe4\xb1\x92\xdf!\x0cXy\xcd\x1b\x8a\xdfv\x10\x9da- M\xf9\x1f\xc3\xb4D\x9d=c\xcdh\xb2\xae\xc4\x14\xff\xc6\xb1\xa3\xac\x81\x01\x90\x00\x00\x00\x00$\x01\x9eb@\xa4\xa5\xbd\xcf\xf0X]\xcacf\x08\xbb(\xb2\x01\xd8\xe9\x13\xef\x85\x16Z\x12H\x95IL\xd6\x0cq\x13\xf8\xa3\xa6\x81\x03 \x00\x00\x00\x00\x1eA\x9ad4@\xa4\x9f\x1c\'\xc7\xd37\xafO\xca\\\xa7\x0c1\xaa\xa0\x81)\x91\x98\xcc\xbf\xf1\xac@\x1cS\xbbk\x97\xbf\x84D\xc6\xab+\xbb\x8f\xb3\x81\x00\xb7\x8a\xf7\x81\x01\xf1\x82\x02j\xf0\x81\t'
    vid_bin = "0001101001000101110111111010001110100011010000101000011010000001000000010100001011110111100000010000000101000010111100101000000100000100010000101111001110000001000010000100001010000010100010000110110101100001011101000111001001101111011100110110101101100001010000101000011110000001000001000100001010000101100000010000001000011000010100111000000001100111000000010000000000000000000000000000000000000000000010000101001100010001010011011001101101110100110000011011111110000100011001101110000001000101110001110100110110111011100010110101001110101011100001000001010101001001101010010110011001010011101011001000000111100101010011011011101110001100010100111010101110000100000101100101010010101110011010110101001110101100100000100000000101010101010011011011101110001100010100111010101110000100000100100101010011000011011001110101001110101100100000100000000111100010010011011011101110001100010100111010101110000100000111000101001110111011011010110101001110101100100000100000100000110111111011000000000100000000000000000000000000000000000000000000000010010110000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000101010100100110101001011001101110101110111111100001000001000001001110000011100010110000101010110101111011000110000011000011110100001001000000011110111010100110000101011101100110100101100100011001010110111101001101100000001000110101001100011000010111011001100110001101010011100000101110001100100011100100101110001100010011000000110000010101110100000110011010010010000110000101101110011001000100001001110010011000010110101101100101001000000011000100101110001100110010111000110011001000000011001000110000001100100011000000110000001101100011000100110101001100000011000001110011101001001001000010011011111100011000001010101100100110101111101000001010101111000110100011000010000011010101001101100110000010010011100000100010010001000110000110001000000010001011011110000000100101011101000111001111100111000000000001000100100010011000100001000000100011110100000000000000000000000000000000000000000000000001011001010100101011100110101101000000100001111011111110000100101100111111011001010110001101011010111000000001000000000000000000000000000000000000000000000000011110001101011110000001000000010111001111000101100000010000000110011100100000010000000000100010101101011001110010000011011101010110111001100100100001101000111101010110010111110100110101010000010001010100011100110100001011110100100101010011010011110010111101000001010101100100001110000011100000010000000100100011111000111000001110000100000010111110101111000010000000001110000000000001000000000000000000000000000000000000000000000000000100101011000010000001001000001011101010000001001000000101010010110000100000010001000001010100101110101000000100001001010101001011001010000001000000110110001110100010101011010000000101001101010000000001111111111111111000010000000000011110011001110100110101000000000111111110110010100100101101111111111000000000001000000000000000010010110101000001100000011000000110010000000000000000000000110000000000000001000000000000000000000011000000000000101010001111000110000011000110010110000000010000000000000100011010001100111000000100111100100001001001010100110000110110011101000000100000101011111110000100010101101000110111000100101111100111001101110011000000010000000000000000000000000000000000000000000000000010111001100011110000000000000100000000000000000000000000000000000000000000000000000000011001111100100000000001000000000000000000000000000000000000000000000000000110100100010110100011100001110100010101001110010000110100111101000100010001010101001001000100100001111000110101001100011000010111011001100110001101010011100000101110001100100011100100101110001100010011000000110000011100110111001100000001000000000000000000000000000000000000000000000000001110100110001111000000000000010000000000000000000000000000000000000000000000000000010001100011110001011000000100000001011001111100100000000001000000000000000000000000000000000000000000000000001000100100010110100011100010000100010001010101010100100100000101010100010010010100111101001110010001001000011110010100001100000011000000111010001100000011000000111010001100000011000100101110001100000011000000110000001100000011000000110000001100000011000000110000000000000000000000011111010000111011011001110101010001011100011110111111100001000100101011111101001111100101000011100111100000010000000010100011010001000110111110000001000000000000000010000000000000000000000000000010111100010000011000000101111111111111111111101101110111000100010111101001101111011110011011011001010010001011011110010110001011001101100000100000110110010010001111101110111011110111100000110010001101100011010000100000001011010010000001100011011011110111001001100101001000000011000100110101001101010010000001110010001100100011100100110001001101110010000000110000011000010011100000110100011001000011100100111000001000000010110100100000010010000010111000110010001101100011010000101111010011010101000001000101010001110010110100110100001000000100000101010110010000110010000001100011011011110110010001100101011000110010000000101101001000000100001101101111011100000111100101101100011001010110011001110100001000000011001000110000001100000011001100101101001100100011000000110001001110000010000000101101001000000110100001110100011101000111000000111010001011110010111101110111011101110111011100101110011101100110100101100100011001010110111101101100011000010110111000101110011011110111001001100111001011110111100000110010001101100011010000101110011010000111010001101101011011000010000000101101001000000110111101110000011101000110100101101111011011100111001100111010001000000110001101100001011000100110000101100011001111010011000000100000011100100110010101100110001111010011000100100000011001000110010101100010011011000110111101100011011010110011110100110000001110100011000000111010001100000010000001100001011011100110000101101100011110010111001101100101001111010011000001111000001100010011101000110000011110000011000100110001001100010010000001101101011001010011110101101000011001010111100000100000011100110111010101100010011011010110010100111101001100100010000001110000011100110111100100111101001100010010000001110000011100110111100101011111011100100110010000111101001100010010111000110000001100000011101000110000001011100011000000110000001000000110110101101001011110000110010101100100010111110111001001100101011001100011110100110000001000000110110101100101010111110111001001100001011011100110011101100101001111010011000100110110001000000110001101101000011100100110111101101101011000010101111101101101011001010011110100110001001000000111010001110010011001010110110001101100011010010111001100111101001100000010000000111000011110000011100001100100011000110111010000111101001100000010000001100011011100010110110100111101001100000010000001100100011001010110000101100100011110100110111101101110011001010011110100110010001100010010110000110001001100010010000001100110011000010111001101110100010111110111000001110011011010110110100101110000001111010011000100100000011000110110100001110010011011110110110101100001010111110111000101110000010111110110111101100110011001100111001101100101011101000011110100110000001000000111010001101000011100100110010101100001011001000111001100111101001100010010000001101100011011110110111101101011011000010110100001100101011000010110010001011111011101000110100001110010011001010110000101100100011100110011110100110001001000000111001101101100011010010110001101100101011001000101111101110100011010000111001001100101011000010110010001110011001111010011000000100000011011100111001000111101001100000010000001100100011001010110001101101001011011010110000101110100011001010011110100110001001000000110100101101110011101000110010101110010011011000110000101100011011001010110010000111101001100000010000001100010011011000111010101110010011000010111100101011111011000110110111101101101011100000110000101110100001111010011000000100000011000110110111101101110011100110111010001110010011000010110100101101110011001010110010001011111011010010110111001110100011100100110000100111101001100000010000001100010011001100111001001100001011011010110010101110011001111010011001100100000011000100101111101110000011110010111001001100001011011010110100101100100001111010011001000100000011000100101111101100001011001000110000101110000011101000011110100110001001000000110001001011111011000100110100101100001011100110011110100110000001000000110010001101001011100100110010101100011011101000011110100110001001000000111011101100101011010010110011101101000011101000110001000111101001100000010000001101111011100000110010101101110010111110110011101101111011100000011110100110000001000000111011101100101011010010110011101101000011101000111000000111101001100000010000001101011011001010111100101101001011011100111010000111101001101010011000000100000011010110110010101111001011010010110111001110100010111110110110101101001011011100011110100110101001000000111001101100011011001010110111001100101011000110111010101110100001111010011010000110000001000000110100101101110011101000111001001100001010111110111001001100101011001100111001001100101011100110110100000111101001100000010000001110010011000110101111101101100011011110110111101101011011000010110100001100101011000010110010000111101001100010011000000100000011100100110001100111101011000110111001001100110001000000110110101100010011101000111001001100101011001010011110100110001001000000110001101110010011001100011110100110010001100100010111000110000001000000111000101100011011011110110110101110000001111010011000000101110001101100011000000100000011100010111000001101101011010010110111000111101001100000010000001110001011100000110110101100001011110000011110100110110001110010010000001110001011100000111001101110100011001010111000000111101001101000010000001110110011000100111011001011111011011010110000101111000011100100110000101110100011001010011110100110001001101000011000000110000001100000010000001110110011000100111011001011111011000100111010101100110011100110110100101111010011001010011110100110001001101000011000000110000001100000010000001100011011100100110011001011111011011010110000101111000001111010011000000101110001100000010000001101110011000010110110001011111011010000111001001100100001111010110111001101111011011100110010100100000011001100110100101101100011011000110010101110010001111010011000000100000011010010111000001011111011100100110000101110100011010010110111100111101001100010010111000110100001100000010000001100001011100010011110100110001001110100011000100101110001100000011000000000000100000000000000000000000000000010111001001100101100010001000010000000010101100010000100010001101000010011101100001110000011111100001011000000000000000010000001100100101000111100001111111010100100110000101010010011000000001010111111100000000011110011000100000000010011000000000000000010000000000011011000000010110001000100001110101011001100000000001101010011001000110000001100000100101001111000100101101000000001101011010110001111101010001101010101011101010000110110101101101111101111111011011000011000010101000001011000011000000000001010000000110101001100000111111111000010100011111000110001011111101100110110000011000001010111000000011101111011110000100101111010100000110100011100000111111000010010111111110010011000010101000000010110111010000000010101101001000000010110001111011011111001000011010010100000010010010010000000011000000001101000011100111010000000000110100100000111011001100001111011100000110011001000111010110011100111000110100100000010010110111100100011000001101001011100011111111110011100111001110101100100011010010000010001010010100001100011101111101010110011101101100011010101011000111110101110111010011001001111010110011010101110111000110011000111011011010011001011000110001001000100000100001000100000101100110010001000001111011011110000101111100001111101011000010010100000011011010111001010001000100101010101110001011110000101000011011101110110000010111001001001110000001010011011110110001110111011101111010011110000100111100001100011001001001011010111111111000110011010101011100110000000010111111111111111100000110001111001000110010000010111010011010000110110100011011111100010011111000000101011100111011011010111011110000011011110000000010101100010010110000111111000110001000111111101011111111001111110010101000000111110100101110111111000111110100010110011001111001001001011011001101101010111111100000000100111111110000100011011011011010110010101010001010111000011111111111010101000011101110111111111100010110110001110010010011000100111101011111010000111111011111100101000111101100110101001101100110000000010010111111101101111111001000101110101100101000011110001110101110110010010001101010000111110111100101110000111110011000000010010100100000100000100000100101001010010100101100011011011010100000001000100110011111001001110101111100101110010111011011010001011000011010110111111110000000000010101111001101011000010110011110110001111000100111001010000110001111000111010110101000010010011011011010101011001101101100000010100100100100010101100101000001111011001001111110001010100000000111110011001011110110110111110000000001101100011110100001011101100010001000100010111001100011011100000011111100010111100110110101111101111101110110011010011010101110000100101111011010110100000110000110111100101000101011100010010000010111100101000011011011101010101100101001011101000011111110000000000101111101101100011000010001010010010011110010001011110011110110000000001101010110100111101001111001111110000010010001111001101011101100100011111011010111001111111000110000100011110011011111111100101000110100000010011101100000010000001001011000000000000000000000000000000000001001010101000001100110100010001100000011001011001001000101111100000011000011001100011000110011011100101101100110000101111001011001111010100010110111011100001000010111000001110011101010001000010000001110010010100010001100010111100100100000000110110101111100010001011010110101001101011101110011000010110010111110100010001110001000000100100010011000110100101100000001010011011001100011101000111000011110100011101001000110000111111100110001101001010011111000100111111110111010110100110010110000001101001101110110101011011101111110001001010101110001100110100000110001010101011011011001100000110111000000011000001000101011011011001011110110100011000000110011111011101111000110000110100111010001100110011000000101100100100001001101010000111101011100101011000011110110100000011001100110000101001110111000011101111000011000110100111010101010100100101010100110100011011110000010010101101111010011110000001010101001001011011000101111001001011111100101011000011011100001001110001000000010100001001100110000100000011010001110101000101010011110000100010000011100101111110001011111000111101010011111010101100110001100010001000011100111111101101001011110000110000110010010101101101011100110011010110011110010011000001010001111010100100000010000000011001000000000000000000000000000000000000100110001000001100111100100000101000000110010110011011101110000100011101100111001001001011011100001000110011001010001100100011000100010000111000000001100110101101111111100001101111010111110111001000110001010001010100001000001110000100111011001010110110100000101001000101011001010110000111010100111001010110011101010010010110101111001001011000110010010110111110010000100001100010110000111100111001101000110111000101011011111011101100001000010011101011000010010110100100000010011011111100100011111110000111011010001000100100111010011110101100011110011010110100010110010101011101100010000010100111111111100011010110001101000111010110010000001000000011001000000000000000000000000000000000000001001000000000110011110011000100100000010100100101001011011110111001111111100000101100001011101110010100110001101100110000010001011101100101000101100100000000111011000111010010001001111101111100001010001011001011010000100100100100010010101010010010100110011010110000011000111000100010011111110001010001110100110100000010000001100100000000000000000000000000000000000000001111001000001100110100110010000110100010000001010010010011111000111000010011111000111110100110011011110101111010011111100101001011100101001110000110000110001101010101010000010000001001010011001000110011000110011001011111111110001101011000100000000011100010100111011101101101011100101111011111110000100010001001100011010101011001010111011101110001111101100111000000100000000101101111000101011110111100000010000000111110001100000100000001001101010111100001000000100001001"
    props = {
        "index": 0,
        "codec_name": "h264",
        "codec_long_name": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
        "profile": "Main",
        "codec_type": "video",
        "codec_time_base": "1/10",
        "codec_tag_string": "[0][0][0][0]",
        "codec_tag": "0x0000",
        "width": 32,
        "height": 32,
        "coded_width": 32,
        "coded_height": 32,
        "has_b_frames": 2,
        "sample_aspect_ratio": "16:9",
        "display_aspect_ratio": "16:9",
        "pix_fmt": "yuv420p",
        "level": 31,
        "color_range": "tv",
        "color_space": "smpte170m",
        "color_transfer": "smpte170m",
        "color_primaries": "smpte170m",
        "chroma_location": "left",
        "field_order": "progressive",
        "refs": 1,
        "is_avc": "true",
        "nal_length_size": "4",
        "r_frame_rate": "5/1",
        "avg_frame_rate": "5/1",
        "time_base": "1/1000",
        "start_pts": 0,
        "start_time": "0.000000",
        "bits_per_raw_sample": "8",
        "disposition": {
            "default": 1,
            "dub": 0,
            "original": 0,
            "comment": 0,
            "lyrics": 0,
            "karaoke": 0,
            "forced": 0,
            "hearing_impaired": 0,
            "visual_impaired": 0,
            "clean_effects": 0,
            "attached_pic": 0,
            "timed_thumbnails": 0,
        },
        "tags": {"DURATION": "00:00:01.000000000"},
    }

    async def setup(self):
        configure_lang({})

    async def test_video(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.Video(
            self.mkv_bytes,
            user_id="user_id",
            user="user",
            target="default",
            connector=mock_connector,
        )

        self.assertEqual(event.user_id, "user_id")
        self.assertEqual(event.user, "user")
        self.assertEqual(event.target, "default")
        self.assertEqual(await event.get_file_bytes(), self.mkv_bytes)
        self.assertEqual(await event.get_mimetype(), "video/x-matroska")
        self.assertEqual(await event.get_properties(), self.props)
        self.assertEqual(await event.get_bin(), self.vid_bin)

    async def test_explicit_mime_type(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.Image(
            self.mkv_bytes,
            user_id="user_id",
            user="user",
            target="default",
            mimetype="video/x-matroska",
            connector=mock_connector,
        )

        self.assertEqual(await event.get_mimetype(), "video/x-matroska")

    async def test_no_mime_type(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        event = events.Image(
            b"aslkdjsalkdjlaj",
            user_id="user_id",
            user="user",
            target="default",
            connector=mock_connector,
        )

        self.assertEqual(await event.get_mimetype(), "")
