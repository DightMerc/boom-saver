import os
import orjson

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


def create_session_maker():
    db_user = os.environ["DB_USER"]
    db_password = os.environ["DB_PASSWORD"]
    db_name = os.environ["DB_NAME"]
    db_host = os.environ["DB_HOST"]
    db_port = os.environ["DB_PORT"]

    engine = create_async_engine(
        f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
        echo=True,
        isolation_level="SERIALIZABLE",
        json_serializer=orjson.dumps,
        json_deserializer=orjson.loads,
    )
    return async_sessionmaker(
        engine,
        autoflush=False,
        expire_on_commit=False,
    )
