import asyncio

from sqlalchemy import Column
from sqlalchemy import MetaData
from sqlalchemy import select
from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import create_async_engine
from datetime import datetime

meta = MetaData()


table = Table(
    "userdata",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("telegram_id", String(100), default=""),
    Column("confidence_ok", Boolean, default=False),
    Column("agreement_ok", Boolean, default=False),
    Column("user_name", String(100), default=""),
    Column("user_contact", String(100), default=""),
    Column("user_age", Integer, default=0),
    Column("is_our_student", Boolean, default=False),
    Column("event_timeslot", DateTime, datetime.datetime(year=2025, month=11, day=15, hour=0, minute=0)),
    Column("registration_ts", DateTime, default=datetime.now()),
    Column("registration_state", Integer, default=0),
)

"""
registration_state
0 - start bot, wait for agreements
10 - confidence accepted
01 - confidence rejected and agreement accepted
11 - agreement accepted
2 - user_name got
3 - user_contact got
4 - user_age got
5 - is_our_student got
6 - event_timeslot got, pending for writing data to spreadsheets
7 - data written to spreadsheets, registration complete
"""


async def async_main() -> None:
    engine = create_async_engine("sqlite+aiosqlite://", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(meta.drop_all)
        await conn.run_sync(meta.create_all)
        await conn.execute(
            table.insert(), [{"telegram_id": "some_name_1"}, {"telegram_id": "some_name_2"}]
        )
    async with engine.connect() as conn:
        # select a Result, which will be delivered with buffered
        # results
        result = await conn.execute(select(table).where(table.c.telegram_id == "some_name_1"))
        print(result.fetchall())
    # for AsyncEngine created in function scope, close and
    # clean-up pooled connections
    await engine.dispose()


asyncio.run(async_main())
