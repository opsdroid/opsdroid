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

    props = "{'index': 0, 'codec_name': 'h264', 'codec_long_name': 'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10', 'profile': 'Main', 'codec_type': 'video', 'codec_time_base': '1/10', 'codec_tag_string': '[0][0][0][0]', 'codec_tag': '0x0000', 'width': 32, 'height': 32, 'coded_width': 32, 'coded_height': 32, 'has_b_frames': 2, 'sample_aspect_ratio': '16:9', 'display_aspect_ratio': '16:9', 'pix_fmt': 'yuv420p', 'level': 31, 'color_range': 'tv', 'color_space': 'smpte170m', 'color_transfer': 'smpte170m', 'color_primaries': 'smpte170m', 'chroma_location': 'left', 'field_order': 'progressive', 'refs': 1, 'is_avc': 'true', 'nal_length_size': '4', 'r_frame_rate': '5/1', 'avg_frame_rate': '5/1', 'time_base': '1/1000', 'start_pts': 0, 'start_time': '0.000000', 'bits_per_raw_sample': '8', 'disposition': {'default': 1, 'dub': 0, 'original': 0, 'comment': 0, 'lyrics': 0, 'karaoke': 0, 'forced': 0, 'hearing_impaired': 0, 'visual_impaired': 0, 'clean_effects': 0, 'attached_pic': 0, 'timed_thumbnails': 0}, 'tags': {'DURATION': '00:00:01.000000000'}}"

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
        self.assertEqual(await str(event.get_properties()), self.props)

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
