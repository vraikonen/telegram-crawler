import asyncio
import time
import logging
import os

from telethon import TelegramClient
from utils.reading_config import reading_config, reading_config_database
from utils.authorization_check import authorize_client
from utils.logging import logging_crawler
from utils.file_io import (
    read_channels_from_file,
    write_pickle,
    read_pickle,
)
from modules.main_crawler import (
    get_entity,
    get_chat_info,
    initialize_mongodb,
    create_index,
    main_get_messages,
    main_get_participants,
)
from modules.alarm import send_email

# Initiate logging
logging_crawler()

# Create the folder for the files created after the first initialization
os.makedirs("temp_var", exist_ok=True)

# Reading Configs
config_telegram = "config/config-username.ini"
api_id, api_hash, phone, username, num_levels = reading_config(config_telegram)

config_database = "config/config-database.ini"
(
    server_path,
    database,
    collection1,
    collection2,
    collection3,
    collection4,
) = reading_config_database(config_database)

# Connect to database and create database and collections
(
    chats_collection,
    messages_collection,
    network_collection,
    participants_collection,
) = initialize_mongodb(
    server_path, database, collection1, collection2, collection3, collection4
)

# Create indexes for the collections
index_messages = [("date", 1), ("peer_id.channel_id", 1)]
index_participants = [("chat_id", 1)]
create_index(messages_collection, index_messages)
create_index(participants_collection, index_participants)

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)

async def main(phone) -> None:
    async with client:
        await client.start()
        logging.info("Client Created")

        # Authorize cient if needed
        me = await authorize_client(client, phone)

        # Reading chats from a text file or from the current iteration
        if os.path.exists("temp_var/entities.pickle"):
            entities = read_pickle("temp_var/entities.pickle")
        else:
            entities = read_channels_from_file("input_chats.txt")
            write_pickle(entities, "temp_var/entities.pickle")
        # Initialize a dictionary for processed chats
        processed_chats = {
            "valid_processed_chats": set(),
            "invalid_processed_chats": set(),
            "valid_processed_entities": set(),
            "invalid_processed_entities": set(),
        }

        # Check if the script run before
        if os.path.exists("temp_var/processed_chats.pickle"):
            processed_chats = read_pickle("temp_var/processed_chats.pickle")

        # Define variables for get_entity() exceptions for request to be awaited
        max_delay_time = 120
        delay_multiplier = 10
        consecutive_errors = 0

        # Initialize iteration number, define iteration time
        iteration_num = 1
        if os.path.exists("temp_var/iteration_num.pickle"):
            iteration_num = read_pickle("temp_var/iteration_num.pickle")
        duration_minutes = 10080  # Set the duration
        end_time = time.time() + duration_minutes * 60

        while time.time() < end_time:
            # Define full_iteration dictionary and all mentions
            full_iteration = {}
            all_mentions = []

            # Check if the script run before
            if os.path.exists("temp_var/full_iteration.pickle"):
                full_iteration = read_pickle("temp_var/full_iteration.pickle")
            if os.path.exists("temp_var/all_mentions.pickle"):
                all_mentions = read_pickle("temp_var/all_mentions.pickle")

            # Skip processed chats
            all_processed = set().union(*processed_chats.values())
            all_processed_list = list(all_processed)
            entities = [item for item in entities if item not in all_processed_list]

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
                    processed_chats["invalid_processed_entities"].add(entity)
                    write_pickle(processed_chats, "temp_var/processed_chats.pickle")
                    # Calculate the delay time based on the consecutive error count
                    delay_time = min(
                        max_delay_time, (consecutive_errors + 1) * delay_multiplier
                    )
                    consecutive_errors += 1
                    await asyncio.sleep(delay_time)
                    continue

                # Getting info about the chat
                try:
                    chat_info = await get_chat_info(
                        client, current_chat, chats_collection
                    )
                except Exception as e:
                    logging.error(
                        f"An error occurred for get_chat_info {current_chat}: {str(e)}"
                    )
                    processed_chats["invalid_processed_chats"].add(current_chat.id)
                    write_pickle(processed_chats, "temp_var/processed_chats.pickle")
                    continue

                # chat_id for the next functions and extracting linked_chat_id for network
                chat_id = chat_info["full_chat"]["id"]
                linked_chat_id = chat_info["full_chat"]["linked_chat_id"]

                # Apply functions for fetching data
                mentioned_chats_full, fwd_from_chats_full = await main_get_messages(
                    iteration_num,
                    full_iteration,
                    chat_id,
                    linked_chat_id,
                    client,
                    messages_collection,
                )

                await main_get_participants(chat_id, client, participants_collection)

                # Write full_iteration
                write_pickle(full_iteration, "temp_var/full_iteration.pickle")

                # Append the values of all mentioned chat types
                all_mentions.extend(mentioned_chats_full)
                all_mentions.extend(fwd_from_chats_full)
                if linked_chat_id is not None:
                    all_mentions.append(linked_chat_id)
                write_pickle(all_mentions, "temp_var/all_mentions.pickle")

                # Add chat id to the processed chats
                processed_chats["valid_processed_chats"].add(chat_id)
                write_pickle(processed_chats, "temp_var/processed_chats.pickle")
                # Add entity to processed entities
                processed_chats["valid_processed_entities"].add(entity)
                write_pickle(processed_chats, "temp_var/processed_chats.pickle")

            # Save current iteration network
            network_collection.insert_one(full_iteration)

            # Define next full iteration entities
            next_iteration = set(all_mentions)
            next_iteration_list = list(next_iteration)
            entities = next_iteration_list
            write_pickle(entities, "temp_var/entities.pickle")

            # Itertion number for the next full iteration is +1
            iteration_num += 1
            write_pickle(iteration_num, "temp_var/iteration_num.pickle")
            # Delete all_mentions and full_iteration - unique for each iteration
            os.remove("temp_var/full_iteration.pickle")
            os.remove("temp_var/all_mentions.pickle")


with client:
    client.loop.run_until_complete(main(phone))

# If disconnected
send_email()
