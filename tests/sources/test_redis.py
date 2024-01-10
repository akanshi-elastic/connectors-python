#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest
from freezegun import freeze_time

from connectors.source import ConfigurableFieldValueError
from connectors.sources.redis import (
    RedisDataSource,
)
from tests.sources.support import create_source

DOCUMENT = [
    {
        "_id": "2d1f1f94982ad0bb733101efb6837577",
        "key": "1",
        "value": "this is value",
        "size_in_bytes": 10,
        "database": 0,
        "key_type": "string",
        "_timestamp": "2023-01-24T04:07:19+00:00",
    },
    {
        "_id": "1f13de8b0b9213fe943efea16823f3e7",
        "key": "2",
        "value": "this is value",
        "size_in_bytes": 10,
        "database": 0,
        "key_type": "string",
        "_timestamp": "2023-01-24T04:07:19+00:00",
    },
    {
        "_id": "0fcabfa8af576ebe76de84b71f9b15ff",
        "key": "1",
        "value": "this is value",
        "size_in_bytes": 10,
        "database": "1",
        "key_type": "string",
        "_timestamp": "2023-01-24T04:07:19+00:00",
    },
    {
        "_id": "975ca8804565c1a569450d61090b2743",
        "key": "2",
        "value": "this is value",
        "size_in_bytes": 10,
        "database": "1",
        "key_type": "string",
        "_timestamp": "2023-01-24T04:07:19+00:00",
    },
]


class RedisObject:
    """Class for mock Redis object"""

    def __init__(self, *args, **kw):
        """Setup document of Mock object"""
        self.db = self

    async def execute_command(self, SELECT="SELECT", db=0):
        return

    async def config_get(self, pattern="databases"):
        return {"databases": "1"}

    async def scan(self, match="*", count=10, _type=None):
        return (0, ["1", "2"])

    async def type(self, *args):  # NOQA
        return "string"

    async def memory_usage(self, *args):
        return 10

    async def get(self, *args):
        return "this is value"

    async def __aenter__(self):
        """Make a dummy connection and return it"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Make sure the dummy connection gets closed"""
        pass


@asynccontextmanager
async def create_redis_source():
    async with create_source(
        RedisDataSource,
        host="localhost",
        port=6379,
        database="0",
        username="username",
        password="password",
    ) as source:
        yield source


@pytest.mark.asyncio
async def test_ping_positive():
    @asynccontextmanager
    async def non_pingable_client():
        redis_mock = Mock()
        redis_mock.ping = AsyncMock(return_value=True)
        yield redis_mock

    async with create_redis_source() as source:
        source.redis_client.client = non_pingable_client
        await source.ping()


@pytest.mark.asyncio
async def test_ping_negative():
    async with create_redis_source() as source:
        with pytest.raises(Exception):
            await source.ping()


@pytest.mark.asyncio
async def test_validate_config_when_database_type():
    async with create_redis_source() as source:
        source.redis_client.database = ["1", "db123", "123"]
        source.ping = AsyncMock(return_value=True)
        with pytest.raises(ConfigurableFieldValueError):
            await source.validate_config()


@pytest.mark.asyncio
async def test_validate_config_when_database_is_invalid():
    async with create_redis_source() as source:
        source.redis_client.database = ["123"]
        with pytest.raises(ConfigurableFieldValueError):
            await source.validate_config()


@pytest.mark.asyncio
@freeze_time("2023-01-24T04:07:19+00:00")
async def test_get_docs():
    async with create_redis_source() as source:
        source.redis_client.database = ["*"]
        mock_redis = RedisObject

        source.redis_client.client = mock_redis
        async for (doc, _) in source.get_docs():
            assert doc in DOCUMENT


@pytest.mark.asyncio
async def test_get_databases_negative():
    async with create_redis_source() as source:
        source.redis_client.database = ["*"]
        databases = await source.redis_client.get_databases()
        assert databases == []
