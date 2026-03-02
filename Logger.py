import logging
import aiofiles
from datetime import datetime
import asyncio

class AsyncLogger:
    def __init__(self, filename="async_app.log"):
        self.filename = filename

    async def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {level} - {message}\n"

        async with aiofiles.open(self.filename, 'a', encoding='utf-8') as f:
            await f.write(log_entry)

        print(log_entry.strip())

    def log_(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {level} - {message}\n"

        with open(self.filename, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        print(log_entry.strip())

# Использование в asyncio
async def main():
    logger = AsyncLogger()
    await logger.log("Асинхронное приложение запущено")
    await logger.log("Выполнена асинхронная операция", "DEBUG")


if __name__ == "__main__":
    asyncio.run(main())