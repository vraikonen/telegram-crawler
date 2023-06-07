print("asfad")

import configparser
import json
import asyncio
import re
import urllib.parse
import os
from datetime import date, datetime

from telethon.errors import UsernameInvalidError
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)



# Functions to parse json date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)


# Reading Configs
config = configparser.ConfigParser()
config.read("config-bastiaugen.ini")

# Setting configuration values
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

api_hash = str(api_hash)

phone = config['Telegram']['phone']
username = config['Telegram']['username']

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)

# Reading number of iterations
num_levels = config.get('Telegram', 'num_levels')
num_levels = int(num_levels)

async def main(phone):
    async with client:
        await client.start()
        print("Client Created")

        # Check if the user is authorized, otherwise initiate the sign-in process
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            try:
                await client.sign_in(phone, input('Enter the code: '))
            except SessionPasswordNeededError:
                await client.sign_in(password=input('Password: '))

        me = await client.get_me()

        # Reading channels from a text file
        with open('input_chats.txt', 'r') as file:
            channels = [line.strip() for line in file]

        level_data = {}  # Dictionary to store level data
        mentioned_channels = channels  # Initialize mentioned channels with input channels
        processed_channels = set()  # Set to keep track of processed channels
        # num_levels = 3

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

                print(f"Current channel is \033[0m{channel}\033[0m")
                try:
                    my_channel = await client.get_entity(entity)
                except ValueError:
                    print(f"\033[0mValueError\033[0m: Cannot find entity corresponding to {entity}")
                    continue
                except UsernameInvalidError:
                    # UsernameInvalidError: Nobody is using this username, or the username is unacceptable.
                    print(f"\033[0mUsernameInvalidError\033[0m: The channel {entity} doesn't exist anymore.")
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

        # Save the level data to a JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_level_data.json"

        with open(filename, "w") as outfile:
            json.dump(level_data, outfile, cls=DateTimeEncoder)

with client:
    client.loop.run_until_complete(main(phone))
