import json
import asyncio
import re
import urllib.parse
from datetime import date, datetime

from telethon.errors import UsernameInvalidError
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)

from utils.reading_config import reading_config
from utils.authorization_check import authorize_client
from modules.saving_netowork import DateTimeEncoder
from modules.saving_netowork import save_level_data
from modules.saving_netowork import read_channels_from_file

# Reading Configs
config_file = 'config/config-bastiaugen.ini'
api_id, api_hash, phone, username, num_levels = reading_config(config_file)

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)


async def main(phone):
    async with client:
        await client.start()
        print("Client Created")

        # Authorize cient
        me = await authorize_client(client, phone)

        # Reading channels from a text file
        channels = read_channels_from_file('input_chats.txt')

        level_data = {}  # Dictionary to store level data
        mentioned_channels = channels  # Initialize mentioned channels with input channels
        processed_channels = set()  # Set to keep track of processed channels

        for level in range(num_levels):
            print(f"level {level}")
            level_key = f"level{level}"
            
            level_data[level_key] = {}  # Create an empty dictionary for the current level
            current_mentioned_channels = mentioned_channels.copy()  # Make a copy of mentioned_channels for the current level
            new_mentioned_channels = [] # Store newly mentioned channels

            # Iterate over the mentioned channels from the previous level
            for channel in current_mentioned_channels:
                if channel.isdigit():
                    entity = PeerChannel(int(channel))
                else:
                    entity = channel

                if entity in processed_channels:
                    continue  # Skip processing this channel if it has already been processed

                print(f"Current channel is {channel}")
                try:
                    my_channel = await client.get_entity(entity)
                except ValueError:
                    print(f"ValueError: Cannot find entity corresponding to {entity}")
                    continue
                except UsernameInvalidError:
                    # UsernameInvalidError: Nobody is using this username, or the username is unacceptable.
                    print(f"UsernameInvalidError: The channel {entity} doesn't exist anymore.")
                    continue

                offset_id = 0
                limit = 100
                filtered_messages = []
                total_messages = 0
                total_count_limit = 0

                # Retrieve channel history
                while True:
                    print("Current Messages Offset ID is:", offset_id, "; Total Mentioned Channels:", total_messages)
                    history = await client(GetHistoryRequest(
                        peer=my_channel,
                        offset_id=offset_id,
                        offset_date=None,
                        add_offset=0,
                        limit=limit,
                        max_id=0,
                        min_id=0,
                        hash=0
                    ))

                    if not history.messages:
                        break

                    messages = history.messages

                    for message in messages:
                        if message.message and "https://t.me/" in message.message:
                            words = message.message.split()
                            filtered_words = [word for word in words if word.startswith("https://t.me/")]
                            for url in filtered_words:
                                channel_name = urllib.parse.urlparse(url).path.split('/')[1]
                                filtered_messages.append(channel_name)
                                new_mentioned_channels.append(channel_name)  # Add newly mentioned channels

                    # Store the filtered messages in the level data dictionary
                    level_data[level_key][channel] = filtered_messages

                    offset_id = messages[-1].id
                    total_messages = len(filtered_messages)
                    if total_count_limit != 0 and total_messages >= total_count_limit:
                        break

                processed_channels.add(entity)  # Mark the current channel as processed

            mentioned_channels.extend(new_mentioned_channels)  # Update mentioned channels with the newly mentioned channels

            # Check if there are no new mentioned channels in the current level
            if len(new_mentioned_channels) == 0:
                break  # Break out of the loop if no new channels were mentioned

        print(f"mentioned channels:{mentioned_channels}")
        print(f"processed channels:{processed_channels}")

        save_level_data(level_data)

with client:
    client.loop.run_until_complete(main(phone))