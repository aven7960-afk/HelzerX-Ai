import asyncio

from helzer.memory import MemoryStore


def test_memory_preserves_turn_order(tmp_path):
    async def run():
        store = MemoryStore(str(tmp_path / "memory.db"), limit=10)
        await store.add("dm:1", 1, "user", "hello", 1)
        await store.add("dm:1", 1, "assistant", "hey", 2)
        assert await store.recent("dm:1") == [("user", "hello"), ("assistant", "hey")]
    asyncio.run(run())
