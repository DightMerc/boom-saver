import logging
from datetime import datetime

from aiogram.types import Message, InlineQuery, ChosenInlineResult
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.application.models import Account, Message as DBMessage
from bot.exceptions import BehaviorException
from db.session import create_session_maker


class BaseController:
    def __init__(self, message: Message):
        self.message = message
        self.user = message.from_user
        self.logger = logging.getLogger(__name__)
        self.session = create_session_maker()
        self.account = None

    async def call(self, *args, **kwargs):
        try:
            self.account = await self._get_or_create_account()
            await self._verify_account()
            await self._update_last_action()
            await self._write_message()
            await self._call(*args, **kwargs)
        except BehaviorException as be:
            default = be.message.get("ru")
            await self.message.answer(
                text=be.message.get(self.user.language_code, default)
            )

    async def _write_message(self):
        async with self.session() as session:
            message_json = str(self.message.model_dump())
            query = insert(DBMessage).values(
                account_id=self.account.id,
                message_text=self.message.text,
                message_json=message_json,
                created_at=datetime.now(),
            )
            await session.execute(query)
            await session.commit()

    async def _update_last_action(self):
        async with self.session() as session:
            query = (
                update(Account)
                .where(Account.id == self.account.id)
                .values(last_action=datetime.now())
            )
            await session.execute(query)
            await session.commit()

    async def _verify_account(self):
        if not self.account.active:
            raise BehaviorException(
                message=dict(
                    ru="Кажется, ты кому-то насолил и тебя блокнули",
                    en="You are blocked.",
                )
            )

    async def _get_or_create_account(self):
        async with self.session() as session:
            session: AsyncSession
            account: Account = (
                await session.scalars(
                    select(Account).filter(Account.telegram_id == str(self.user.id))
                )
            ).first()
        if not account:
            return await self._create_account()
        return account

    async def _create_account(self):
        async with self.session() as session:
            session: AsyncSession
            query = insert(Account).values(
                first_name=self.user.first_name,
                username=self.user.username,
                telegram_id=str(self.user.id),
                is_bot=self.user.is_bot,
                is_premium=self.user.is_premium,
                active=True,
                account_type="private",
                created_at=datetime.now(),
                last_action=datetime.now(),
            )
            result = await session.execute(query)
            await session.commit()
            account_id: int = result.inserted_primary_key[0]
            return await self._get_account_by_id(account_id=account_id)

    async def _get_account_by_id(self, account_id: int) -> Account:
        async with self.session() as session:
            session: AsyncSession
            account: Account = (
                await session.scalars(select(Account).filter(Account.id == account_id))
            ).first()
            return account


class BaseInlineController:
    def __init__(self, query: InlineQuery):
        self.query = query
        self.logger = logging.getLogger(__name__)

    async def call(self, *args, **kwargs):
        await self._call(*args, **kwargs)


class BaseInlineResultController:
    def __init__(self, result: ChosenInlineResult):
        self.result = result
        self.logger = logging.getLogger(__name__)

    async def call(self, *args, **kwargs):
        await self._call(*args, **kwargs)
