import asyncio
import logging

from telethon import errors

from modules.main_crawler import (
    get_entity,
    get_chat_info,
    main_get_messages_mentions,
    main_get_participants,
    write_processed,
)

from modules.alarm import send_email


# Main logic for processing chats
async def process_chats(
    client,
    client_details,
    queue,
    processed_chats_collection,
    iteration_num,
    chats_collection,
    messages_collection,
    network_collection,
    participants_collection,
):
    """
    Asynchronous function for processing multiple Telegram chats.

    This function is responsible for processing multiple Telegram chats asynchronously.
    It takes a Telegram client, a queue of chat entities to process, and various MongoDB collections
    to store the processed data. It connects to each chat, retrieves information about the chat,
    and applies functions to fetch messages, mentions, and participants. The processed data is then
    stored in the specified MongoDB collections.

    Parameters:
    - client (TelegramClient): The Telegram client.
    - client_details (dict): A dictionary containing details about the clients' connection status.
    - queue (asyncio.Queue): An asynchronous queue containing chat entities to process.
    - processed_chats_collection: The MongoDB collection for storing processed chat information.
    - iteration_num: The iteration number associated with the iteration.
    - chats_collection: The MongoDB collection for storing chat information.
    - messages_collection: The MongoDB collection for storing message information.
    - network_collection: The MongoDB collection for storing network (mentioned chats) information.
    - participants_collection: The MongoDB collection for storing participant information.

    Returns:
    None

    Note:
    - The function processes each chat entity in the provided queue until there are no more entities.
    - It uses other functions (`get_entity`, `get_chat_info`, `main_get_messages_mentions`, `main_get_participants`)
    to retrieve information about the chat and fetch messages and participants.
    - The function handles exceptions such as `FloodWaitError` and logs errors accordingly.
    If a `FloodWaitError` occurs, the function puts the entity back into the queue, sets the client's status to "Sleeping,"
    logs the error, and sleeps for the specified duration. It monitors the disconnection status of other clients during this time.
    If other clients are disconnected, the function exits the loop before the specified duration.

    """
    async with client:
        await client.start()
        client_details[client][2] = "Connected"
        # Define variables for get_entity() exceptions for request to be awaited
        max_delay_time = 120
        delay_multiplier = 10
        consecutive_errors = 0

        await queue.put("Fake entity to inform there are no entities left")
        while True:
            entity = await queue.get()  # Get an entity from the queue
            print(f"Processing entity: {entity}...")
            if entity == "Fake entity to inform there are no entities left":
                break  # No more entities to process

            # Creating first connection with the chat
            try:
                current_chat = await get_entity(client, entity)
                logging.info(
                    f"Current processing chat is: {current_chat.id} {client_details[client]}"
                )
                consecutive_errors = 0  # Reset error count
            except errors.FloodWaitError as e:
                await queue.put(entity)
                client_details[client][2] = "Sleeping"
                logging.error(
                    f"Flood wait error for get_entity {entity}: {str(e)}. Client: {client_details[client]} is sleeping."
                )

                # Await FloodWaitError, exit the task if other clients are out
                start_time = asyncio.get_event_loop().time()
                while asyncio.get_event_loop().time() - start_time < (e.seconds + 60):
                    print("Checking...")
                    if any(
                        value[2] == "Disconnected" for value in client_details.values()
                    ):
                        break
                    print("No need to exit the loop.")
                    await asyncio.sleep(900)

                client_details[client][2] = "Connected"
                continue
            except Exception as e:
                logging.error(f"An error occurred for get_entity {entity}: {str(e)}")
                # Mark chat as processed
                write_processed(
                    processed_chats_collection,
                    iteration_num,
                    entity,
                    None,
                    type="invalid_entity",
                )
                # Calculate the delay time based on the consecutive error count
                delay_time = min(
                    max_delay_time, (consecutive_errors + 1) * delay_multiplier
                )
                consecutive_errors += 1
                await asyncio.sleep(delay_time)
                continue

            # Getting info about the chat
            try:
                chat_info = await get_chat_info(client, current_chat, chats_collection)
            except Exception as e:
                logging.error(
                    f"An error occurred for get_chat_info {current_chat}: {str(e)}"
                )
                # Mark chat as processed
                write_processed(
                    processed_chats_collection,
                    iteration_num,
                    entity,
                    current_chat.id,
                    type="invalid_chat",
                )
                continue

            # chat_id for the next functions and extracting linked_chat_id for network
            chat_id = chat_info["full_chat"]["id"]
            linked_chat_id = chat_info["full_chat"]["linked_chat_id"]

            # Apply functions for fetching data
            await main_get_messages_mentions(
                iteration_num,
                chat_id,
                linked_chat_id,
                client,
                messages_collection,
                network_collection,
            )
            await main_get_participants(chat_id, client, participants_collection)

            # Mark chat as processed
            write_processed(
                processed_chats_collection, iteration_num, entity, chat_id, type="valid"
            )

        client.disconnect()
        client_details[client][2] = "Disconnected"
