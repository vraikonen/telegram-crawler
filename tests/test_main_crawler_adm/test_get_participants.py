import os
import sys
import pytest
import asyncio
from telethon import TelegramClient
from telethon.tl.types import PeerChannel


from utils.reading_config import reading_config
from utils.authorization_check import authorize_client
from modules.main_crawler import get_entity, get_chat_info, get_participants

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

        participants = await get_participants(client, chat_id)

        # Define the phone number and ID you want to check for
        desired_phone = "4367764863157"
        desired_id = 5963929426

        # Check if the desired participant exists in the participants dictionary
        for chat_id, chat_participants in participants.items():
            for participant in chat_participants:
                if (
                    participant.get("id") == desired_id
                    and participant.get("phone") == desired_phone
                ):
                    # The desired participant is found, the test passes
                    break
            else:
                # The loop did not break, meaning the desired participant is not found
                # The test fails
                assert False

        # If the loop completes without breaking, the desired participant is found, the test passes
        assert True
