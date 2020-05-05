import asynctest
import asynctest.mock as mock

from opsdroid.memory import Memory
from opsdroid.database import InMemoryDatabase


class TestMemory(asynctest.TestCase):
    """Test the opsdroid memory class."""

    def setup(self):
        mem = Memory()
        mem.databases = [InMemoryDatabase()]
        return mem

    async def test_memory(self):
        memory = self.setup()
        data = "Hello world!"
        await memory.put("test", data)
        self.assertEqual(data, await memory.get("test"))
        await memory.delete("test")
        self.assertIsNone(await memory.get("test"))

    async def test_empty_memory(self):
        memory = self.setup()
        self.assertEqual(None, await memory.get("test"))

    async def test_database_callouts(self):
        memory = self.setup()
        memory.databases = [mock.MagicMock()]
        memory.databases[0].get = mock.CoroutineMock()
        memory.databases[0].put = mock.CoroutineMock()
        memory.databases[0].delete = mock.CoroutineMock()
        data = "Hello world!"

        await memory.put("test", data)
        self.assertTrue(memory.databases[0].put.called)

        memory.databases[0].reset_mock()

        await memory.get("test")
        self.assertTrue(memory.databases[0].get.called)

        memory.databases[0].reset_mock()
        await memory.delete("test")
        self.assertTrue(memory.databases[0].delete.called)
