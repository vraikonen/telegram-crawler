import os
import sys
import pytest
import asyncio
from telethon import TelegramClient
from telethon.tl.types import PeerChannel

from utils.reading_config import reading_config
from utils.authorization_check import authorize_client
from modules.main_crawler import get_entity

# Add the project's root directory to sys.path
current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, root_dir)


# Reading Configs
config_file = os.path.join(root_dir, "config", "config-bastiaugen.ini")
api_id, api_hash, phone, username, num_levels = reading_config(config_file)


# Create a fixture for the TelegramClient
@pytest.fixture
async def client_fixture():
    async with TelegramClient(username, api_id, api_hash) as client:
        yield client


# Create a fixture to provide the entity for testing
@pytest.fixture
def test_entity():
    return "test_bastian"


@pytest.mark.asyncio
async def test_get_entity(client_fixture, test_entity):
    async for client in client_fixture:
        result = await get_entity(client, test_entity)
        assert result.username == test_entity
        assert result.id == 1318919825
        assert result.noforwards is False
