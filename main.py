import asyncio
import time
import logging

from telethon import TelegramClient

from utils.reading_config import reading_config, reading_config_database
from utils.authorization_check import authorize_client
from utils.logging import logging_crawler
from modules.saving_netowork import read_channels_from_file
from modules.main_crawler import (
    get_entity,
    get_chat_info,
    initialize_mongodb,
    create_index,
    main_get_messages,
    main_get_participants
)
from modules.alarm import send_email

# Initiate logging
logging_crawler()

# Reading Configs
config_telegram = "config/config-username.ini"
api_id, api_hash, phone, username, num_levels = reading_config(config_telegram)

config_database = "config/config-database.ini"
(server_path, database, collection1, collection2, collection3, collection4
 ) = reading_config_database(config_database)

# Connect to database and create database and collections
(chats_collection, messages_collection, network_collection, participants_collection
 ) = initialize_mongodb(
    server_path, database, collection1, collection2, collection3, collection4)

# Create indexes for the collections
index_messages = [("date", 1), ("peer_id.channel_id", 1)]
index_participants = [("chat_id", 1)]
create_index(messages_collection, index_messages)
create_index(participants_collection, index_participants)

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)

async def main(phone):
    async with client:
        await client.start()
        logging.info("Client Created")

        # Authorize cient if needed
        me = await authorize_client(client, phone)

        # Reading chats from a text file
        entities = read_channels_from_file("input_chats.txt")

        # Initialize a set for processed chats
        processed_chats = set()

        # Define variables for get_entity() exceptions for request to be awaited
        max_delay_time = 60
        delay_multiplier = 5
        consecutive_errors = 0

        # Initialize iteration number, define iteration time
        iteration_num = 1
        duration_minutes = 10080  # Set the duration
        end_time = time.time() + duration_minutes * 60

        while time.time() < end_time:
            # Define full_iteration dictionary which will be overwritten with each 
            # new full iteration (iteration over all input chats),
            # as well as all_mentions which will be used for next full iteration
            full_iteration = {}
            all_mentions = []

            # Main code: Iterating over input/mentioned chats
            for entity in entities:
                # Creating first connection with the chat
                try:
                    current_chat = await get_entity(client, entity)
                    logging.info(f"Current processing chat is: {current_chat.id}")
                    # Reset the consecutive error count to 0 if the operation is successful
                    consecutive_errors = 0
                except Exception as e:
                    logging.error(
                        f"An error occurred for get_entity {entity}: {str(e)}"
                    )
                    # Calculate the delay time based on the consecutive error count
                    delay_time = min(
                        max_delay_time, (consecutive_errors + 1) * delay_multiplier
                    )
                    consecutive_errors += 1
                    await asyncio.sleep(delay_time)
                    continue

                # Skipping proccessed entities before get_chat_info() because it produces rate limits
                if current_chat.id in processed_chats:
                    logging.info(
                        f"Chat {current_chat.id} has already been processed. Skipping..."
                    )
                    continue

                try:
                    chat_info = await get_chat_info(
                        client, current_chat, chats_collection
                    )
                    # append_data_to_json(chat_info, 'chat_info.json')
                except Exception as e:
                    logging.error(
                        f"An error occurred for get_chat_info {current_chat}: {str(e)}"
                    )
                    continue

                ### CHECK THIS SECTION WHEN YOU LATER WANT TO SAVE CHAT INFO DIFFERENTELY
                # Getting chat_id from chat_info used in data retrieval; 
                # linked_chat_id is always a group linked to a channel or vice versa
                chat_id = chat_info["full_chat"]["id"]
                linked_chat_id = chat_info["full_chat"]["linked_chat_id"]

                # Apply functions for fetching data
                mentioned_chats_full, fwd_from_chats_full = await main_get_messages(
                    iteration_num, full_iteration, chat_id, linked_chat_id, client, messages_collection)

                await main_get_participants(chat_id,client,participants_collection)

                # Add chat id to the processed chats
                processed_chats.add(chat_id)
                # Append the values of all mentioned chat types
                all_mentions.extend(mentioned_chats_full)
                all_mentions.extend(fwd_from_chats_full)
                if linked_chat_id is not None:
                    all_mentions.append(linked_chat_id)

            network_collection.insert_one(full_iteration)

            # Define next full iteration entities
            next_iteration = set(all_mentions)
            next_iteration_list = list(next_iteration)
            entities = next_iteration_list

            # Itertion number for the next full iteration is +1
            iteration_num += 1



with client:
    client.loop.run_until_complete(main(phone))

# If disconnected
send_email()
