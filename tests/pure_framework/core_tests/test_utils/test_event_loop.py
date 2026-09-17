import asyncio
import unittest

from core.utils.event_loop import get_or_create_event_loop


class TestEventLoop(unittest.TestCase):
    def setUp(self):
        try:
            self.previous_loop = asyncio.get_event_loop()
        except RuntimeError:
            self.previous_loop = None
        asyncio.set_event_loop(None)
        self.loops = []

    def tearDown(self):
        for loop in self.loops:
            loop.close()
        asyncio.set_event_loop(self.previous_loop)

    def test_creates_and_reuses_current_loop(self):
        loop = get_or_create_event_loop()
        self.loops.append(loop)
        self.assertIs(loop, asyncio.get_event_loop())
        self.assertIs(loop, get_or_create_event_loop())

    def test_replaces_closed_loop(self):
        closed_loop = get_or_create_event_loop()
        closed_loop.close()
        loop = get_or_create_event_loop()
        self.loops.append(loop)
        self.assertIsNot(loop, closed_loop)
        self.assertFalse(loop.is_closed())
        self.assertIs(loop, asyncio.get_event_loop())

    def test_preserves_running_loop(self):
        async def check_loop():
            self.assertIs(get_or_create_event_loop(), asyncio.get_running_loop())

        asyncio.run(check_loop())

    def test_creates_loop_after_asyncio_run(self):
        async def task():
            return 42

        self.assertEqual(asyncio.run(task()), 42)
        loop = get_or_create_event_loop()
        self.loops.append(loop)
        self.assertEqual(loop.run_until_complete(task()), 42)
