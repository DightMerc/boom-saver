from sqlalchemy import (
    Integer,
    String,
    Column,
    MetaData,
    Table,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import registry

from bot.application.models import Account, Message, File

metadata_obj = MetaData()
mapper_registry = registry()

accounts = Table(
    "accounts",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("first_name", String()),
    Column("username", String()),
    Column("telegram_id", String()),
    Column("is_bot", Boolean()),
    Column("is_premium", Boolean()),
    Column("active", Boolean()),
    Column("account_type", String()),
    Column("created_at", DateTime()),
    Column("last_action", DateTime()),
)

messages = Table(
    "messages",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("account_id", Integer, ForeignKey("accounts.id"), nullable=False),
    Column("message_text", String()),
    Column("message_json", String()),
    Column("created_at", DateTime()),
)

files = Table(
    "files",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("account_id", Integer, ForeignKey("accounts.id"), nullable=False),
    Column("link", String()),
    Column("file_id", String()),
    Column("file_info", String()),
    Column("created_at", DateTime()),
)

mapper_registry.map_imperatively(Account, accounts)
mapper_registry.map_imperatively(Message, messages)
mapper_registry.map_imperatively(File, files)
