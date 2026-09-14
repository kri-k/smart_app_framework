import asyncio


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """Возвращает текущий event loop потока, создавая новый при его отсутствии.

    Начиная с Python 3.14 ``asyncio.get_event_loop()`` больше не создаёт
    новый loop неявно и выбрасывает ``RuntimeError``, если в потоке нет
    текущего loop. Эта функция сохраняет прежнее поведение для мест, где
    loop нужен вне корутины (например, при синхронной инициализации).
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop
