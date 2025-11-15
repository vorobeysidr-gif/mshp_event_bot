import asyncio

from sqlalchemy import Column
from sqlalchemy import MetaData
from sqlalchemy import select
from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import create_async_engine
from datetime import datetime

from enum import Enum

meta = MetaData()


user_table = Table(
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

timeslot_table = Table(
    "timeslotdata",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("description", String(255), default=""),
    Column("timestamp", DateTime),
    Column("is_active", Boolean, default=True),
)

class RegistrationState(Enum):
    START_BOT = 0
    WAIT_FOR_CONFIDENCE_AND_AGREEMENT = 100
    CONFIDENCE_ACCEPTED = 110
    CONFIDENCE_REJECTED_AND_AGREEMENT_ACCEPTED = 101
    BOTH_CONFIDENCE_AND_AGREEMENT_ACCEPTED = 111
    WAIT_FOR_USER_NAME = 2
    WAIT_FOR_USER_CONTACT = 3
    WAIT_FOR_USER_AGE = 4
    WAIT_FOR_IS_OUR_STUDENT = 5
    WAIT_FOR_EVENT_TIMESLOT = 6
    WAIT_FOR_DATA_WRITTEN_TO_SPREADSHEETS = 7
    DATA_WRITTEN_TO_SPREADSHEETS = 8


async def async_main() -> None:
    engine = create_async_engine("sqlite+aiosqlite://", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(meta.drop_all)
        await conn.run_sync(meta.create_all)
        await conn.execute(
            user_table.insert(), [{"telegram_id": "some_name_1"}, {"telegram_id": "some_name_2"}]
        )
    async with engine.connect() as conn:
        # select a Result, which will be delivered with buffered
        # results
        result = await conn.execute(select(user_table).where(user_table.c.telegram_id == "some_name_1"))
        print(result.fetchall())
    # for AsyncEngine created in function scope, close and
    # clean-up pooled connections
    await engine.dispose()


asyncio.run(async_main())
