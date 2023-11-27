import os
import sys
import pytest
import asyncio
from telethon import TelegramClient
from telethon.tl.types import PeerChannel

from utils.reading_config import reading_config
from utils.authorization_check import authorize_client
from modules.main_crawler import (
    get_entity,
    get_chat_info,
    get_messages,
    get_fwd_from,
    get_mentioned_chats,
)

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
async def test_get_chat_info(client_fixture, test_entity):
    async for client in client_fixture:
        current_chat = await get_entity(client, test_entity)

        chat_info = await get_chat_info(client, current_chat)
        chat_id = chat_info["full_chat"]["id"]

        messages, mentioned_chats_full, fwd_from_chats_full = await get_messages(
            client, chat_id
        )
        assert isinstance(messages, list)
        assert isinstance(mentioned_chats_full, list)
        assert isinstance(fwd_from_chats_full, list)

        # Check content of any message that you are aware of existance
        desired_content = "@t.me/putinistrussia"
        desired_message_found = any(
            message.get("message") == desired_content for message in messages
        )
        assert desired_message_found is True

        # Check if there is a mentioned chat for which you are sure there is
        desired_mention = "covid_vaccine_injuries"
        desired_mention_found = any(
            mention == desired_mention for mention in mentioned_chats_full
        )
        assert desired_mention_found is True

        # Check fwd from, for example, we know that we fwd to our group from this username: test_channel_bastian
        test_entity = "test_channel_bastian"
        current_chat = await get_entity(client, test_entity)
        chat_id = current_chat.id
        assert chat_id in fwd_from_chats_full
