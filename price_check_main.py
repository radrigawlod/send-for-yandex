import asyncio, datetime, schedule
from Handlers.YDBPriceHandler import YDB
import VkusVill
from Handlers.Logger import AsyncLogger

async def vv_main(ydb, logger):
    await VkusVill.main(ydb, logger, update=True)

async def main():
    ydb = YDB()
    logger = AsyncLogger()
    await vv_main(ydb, logger)

async def scheduler():
    schedule.every().day.at("13:00").do(lambda: asyncio.create_task(main()))

    while True:
        schedule.run_pending()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())


# 0677951
import matplotlib.pyplot as plt