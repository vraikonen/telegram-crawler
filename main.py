import asyncio
import time
import os
import sys

from utils.reading_config import reading_config_database, initialize_clients
from utils.authorization_check import authorize_clients
from utils.logging import logging_crawler, custom_exception_hook
from utils.file_io import (
    read_channels_from_file,
    write_pickle,
    read_pickle,
)
from modules.main_crawler import (
    initialize_mongodb,
    create_index,
)
from modules.alarm import send_email

from modules.chat_processing_logic import process_chats


async def main_entry_point():
    # Reading chats from a text file or from the last iteration
    if os.path.exists("temp_var/entities.pickle"):
        entities = read_pickle("temp_var/entities.pickle")
    else:
        entities = read_channels_from_file("config/input_chats.txt")
        entities = [
            word.casefold() if isinstance(word, str) else word for word in entities
        ]
        entities = list(set(entities))
        write_pickle(entities, "temp_var/entities.pickle")

    for client in clients:
        await authorize_clients(client, client_details)

    # Initialize iteration number, define processing time
    iteration_num = 1
    if os.path.exists("temp_var/iteration_num.pickle"):
        iteration_num = read_pickle("temp_var/iteration_num.pickle")
    end_time = (
        time.time() + int(max_run_time) * 60
    )  # Set the duration in config-database

    while time.time() < end_time:
        # Gather processed chats
        cursor = processed_chats_collection.find({}, {"chat_id": 1, "username": 1})
        processed_chats_list = []
        for document in cursor:
            processed_chats_list.append(document["chat_id"])
            processed_chats_list.append(document["username"])
        processed_chats_list = [
            word.casefold() if isinstance(word, str) else word
            for word in processed_chats_list
        ]
        processed_chats_list = list(set(processed_chats_list))

        # Skip entities if they were processed in the previous iterations
        entities = [item for item in entities if item not in processed_chats_list]
        # Exit the loop if there are no more entities
        if not entities:
            break
        # Create and populate a shared queue
        shared_queue = asyncio.Queue()
        for entity in entities:
            await shared_queue.put(entity)

        # Create tasks for processing entities for each client
        processing_tasks = [
            process_chats(
                client,
                client_details,
                shared_queue,
                processed_chats_collection,
                iteration_num,
                chats_collection,
                messages_collection,
                network_collection,
                participants_collection,
            )
            for client in clients
        ]

        # Run all tasks concurrently
        await asyncio.gather(*processing_tasks)

        # Gather chats for next iteration
        cursor = network_collection.find(
            {"iteration_num": iteration_num},
            {
                "mentions_with_tdotme": 1,
                "mentions_with_at": 1,
                "fwd_from": 1,
                "linked": 1,
            },
        )
        all_mentions = []
        for document in cursor:
            all_mentions.extend(document["mentions_with_tdotme"])
            all_mentions.extend(document["mentions_with_at"])
            all_mentions.extend(document["fwd_from"])
            all_mentions.append(document["linked"])

        all_mentions = [
            word.casefold() if isinstance(word, str) else word for word in all_mentions
        ]
        entities = list(set(all_mentions))
        write_pickle(entities, "temp_var/entities.pickle")

        # Itertion number for the next full iteration is +1
        iteration_num += 1
        write_pickle(iteration_num, "temp_var/iteration_num.pickle")
        if iteration_num == int(max_iterations):
            break


if __name__ == "__main__":
    # Initiate logging, set the custom exception hook
    logging_crawler()
    sys.excepthook = custom_exception_hook

    # Create the folder for the files created after the first initialization
    os.makedirs("temp_var", exist_ok=True)

    # Read Configs and create Telegram client objects (no conenction yet)
    clients, client_details = initialize_clients()

    config_database = "config/config-database-script-params.ini"
    (
        server_path,
        database,
        collection1,
        collection2,
        collection3,
        collection4,
        collection5,
        max_run_time,
        max_iterations,
    ) = reading_config_database(config_database)

    # Connect to database and create database and collections
    (
        chats_collection,
        messages_collection,
        network_collection,
        participants_collection,
        processed_chats_collection,
    ) = initialize_mongodb(
        server_path,
        database,
        collection1,
        collection2,
        collection3,
        collection4,
        collection5,
    )

    # Create indexes for the collections
    index_messages1 = [("date", 1)]
    index_messages2 = [("peer_id.channel_id", 1)]
    index_participants = [("chat_id", 1)]
    create_index(messages_collection, index_messages1)
    create_index(messages_collection, index_messages2)
    create_index(participants_collection, index_participants)

    # Run the asynchronous event loop
    asyncio.run(main_entry_point())
