from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass
class Account:
    id: int
    first_name: str
    username: str
    telegram_id: str
    is_bot: bool
    is_premium: bool
    active: bool
    account_type: str
    created_at: datetime
    last_action: datetime


@dataclass
class Message:
    id: int
    account_id: int
    message_text: str
    message_json: str
    created_at: datetime


@dataclass
class File:
    id: int
    account_id: int
    link: str
    file_id: str
    file_info: str
    created_at: str
