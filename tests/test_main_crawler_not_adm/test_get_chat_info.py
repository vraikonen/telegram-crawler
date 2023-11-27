import os
import sys
import pytest
import asyncio
from telethon import TelegramClient
from telethon.tl.types import PeerChannel

from utils.reading_config import reading_config
from utils.authorization_check import authorize_client
from modules.main_crawler import get_entity, get_chat_info

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
    return "https://t.me/davids_meme_channel"


@pytest.mark.asyncio
async def test_get_chat_info(client_fixture, test_entity):
    async for client in client_fixture:
        current_chat = await get_entity(client, test_entity)

        chat_info = await get_chat_info(client, current_chat)
        assert chat_info is not None
        assert chat_info["full_chat"]["id"] == 1920077960
        assert chat_info["full_chat"]["about"] == "Definitely not for work"
