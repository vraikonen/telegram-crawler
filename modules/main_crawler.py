import asyncio
import re
import logging
import pymongo

from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.types import (
    PeerChannel,
    PeerChat,
    MessageFwdHeader,
    ChannelParticipantsSearch,
)
from telethon.tl import functions, types


def initialize_mongodb(
    server_path,
    database,
    collection1,
    collection2,
    collection3,
    collection4,
    collection5,
):
    """
    Initializes a connection to a MongoDB server and returns specified collections.

    This function establishes a connection to a MongoDB server, accesses/creates a database named 'database',
    as well as accesses/creates five collections.

    Parameters are located in config file.

    Parameters:
    - server_path (str): The MongoDB server path.
    - database (str): The name of the MongoDB database.
    - collection1 (str): The name of the first collection.
    - collection2 (str): The name of the second collection.
    - collection3 (str): The name of the third collection.
    - collection4 (str): The name of the fourth collection.
    - collection5 (str): The name of the fifth collection.

    Returns:
    tuple: A tuple containing the specified MongoDB collections (collection1 to collection5).
    """
    # Initialize the MongoDB client
    myclient = pymongo.MongoClient(server_path)
    logging.info(f"Connection established with: {server_path}")

    # Access or create the database
    db = myclient[database]

    # Access or create the collections
    collection1 = db[collection1]
    collection2 = db[collection2]
    collection3 = db[collection3]
    collection4 = db[collection4]
    collection5 = db[collection5]

    # Return the collections
    return collection1, collection2, collection3, collection4, collection5


# Define an asynchronous lock
lock = asyncio.Lock()


# Writing in the database
async def write_data(data, collection_name):
    """
    Writes data to a MongoDB collection in an asynchronous manner.

    This asynchronous function writes data to the specified MongoDB collection in a safe and
    thread-safe manner using an asynchronous lock. The 'data' parameter should be a dictionary
    or a list of dictionaries.

    Parameters:
    - data: The data to be written to the MongoDB collection.
    - collection_name: The MongoDB collection to write data to.

    Returns:
    None
    """
    try:
        async with lock:
            # Insert the data into the collection
            # Data should be a dictionary or a list of dictionaries
            if isinstance(data, dict):
                # Insert a single document
                collection_name.insert_one(data)
            elif isinstance(data, list):
                # Insert multiple documents
                collection_name.insert_many(data)
            else:
                logging.info(
                    f"Probably wrong data type, it should be dictionary or list of dictionaries!"
                )
    except Exception as e:
        logging.error(f"An error occurred for write_data(): {str(e)}")


# Creating indeces
def create_index(collection, index):
    """
    Creates an index in a MongoDB collection.

    This function creates an index in the specified MongoDB collection using the provided 'index'.
    The 'index' parameter should be a dictionary defining the fields and their ordering for the index.

    Parameters:
    - collection: The MongoDB collection in which the index will be created.
    - index: A dictionary specifying the fields and ordering for the index.

    Returns:
    None
    """
    try:
        collection.create_index(index, unique=False)
    except Exception as e:
        logging.error(f"Error creating index in {collection}: {str(e)}")


def write_processed(collection, iteration_num, entity, chat_id, type, error):
    """
    Writes processed chat to a MongoDB collection.

    This function inserts a document into the specified MongoDB collection with information
    about processed chat, including 'iteration_num', 'type', 'entity', and 'chat_id'.

    Parameters:
    - collection: The MongoDB collection to write processed chat to.
    - iteration_num: The iteration number associated with the processed chat.
    - entity: The username associated with the processed chat.
    - chat_id: The chat ID associated with the processed chat.
    - type: The validity of processed chat.

    Returns:
    None
    """
    collection.insert_one(
        {
            "iteration_num": iteration_num,
            "username": entity,
            "chat_id": chat_id,
            "type": type,
            "error": error,
        }
    )


# First connection to the chat
async def get_entity(client, entity):
    """
    Retrieves the chat entity using the Telegram client.

    This asynchronous function retrieves information about the specified chat entity using the
    Telegram client. If the 'entity' parameter is a digit, it is treated as a channel ID.

    Parameters:
    - client (TelegramClient): The Telegram client.
    - entity: The entity (user, chat, channel) from which to retrieve information. It can be a username,
    a chat ID, or a channel ID.

    Returns:
    Telegram entity: The entity as returned by the `get_entity` method.
    More about entity object: https://docs.telethon.dev/en/stable/concepts/entities.html.
    """
    if str(entity).isdigit():
        entity = PeerChannel(int(entity))
    else:
        entity = entity
    current_chat = await client.get_entity(entity)
    return current_chat


# Getting further information about the chat
async def get_chat_info(client, current_chat, chats_collection):
    """
    Retrieves additional information about the chat and writes it to a MongoDB collection.

    Parameters:
    - client (TelegramClient): The Telegram client.
    - current_chat: The entity object from modules.main_crawler.get_entity(), to retrieve additional information.
    - chats_collection: The MongoDB collection where the chat information will be stored.

    Returns:
    dict: A dictionary containing the retrieved chat information.
    Note: More about retrieved chat object: https://core.telegram.org/type/chat.
    """
    chat_full = await client(GetFullChannelRequest(current_chat))
    chat_dict = chat_full.to_dict()
    await write_data(chat_dict, chats_collection)
    return chat_dict


async def get_participants(client, chat, participants_collection):
    """
    Retrieves participants of a Telegram chat and writes the data to a MongoDB collection.

    Parameters:
    - client (TelegramClient): The Telegram client.
    - chat: The chat entity for which to retrieve participants (chat_id or entity object).
    - participants_collection: The MongoDB collection where the participant information will be stored.

    Returns:
    None

    Note:
    More about telegram particpant object: https://core.telegram.org/type/ChannelParticipant.
    """
    limit = 100
    offset = 0
    all_participants = []

    print("Retrieving participants...")
    while True:
        participants = await client(
            GetParticipantsRequest(
                chat, ChannelParticipantsSearch(""), offset, limit, hash=0
            )
        )
        if not participants.users:
            break
        for participant in participants.users:
            participant_data = participant.to_dict()
            participant_data["chat_id"] = chat
            all_participants.append(participant_data)
        offset += len(participants.users)
    print(f"Number of collected participants: {len(all_participants)}")

    await write_data(all_participants, participants_collection)


def get_fwd_from(message):
    """
    Extracts forwarded chat IDs from a Telegram message.
    It adds the ID to the list of forwarded chats.

    Parameters:
    - message (Message): The Telegram message object.

    Returns:
    list: A list of forwarded chat IDs extracted from the message.

    Note:
    Telegram message object can eventually have different endpoint.
    More about message object: https://core.telegram.org/type/Message.

    """
    fwd_from_chats = []

    fwd_from = message.fwd_from
    if fwd_from and isinstance(fwd_from, MessageFwdHeader):
        from_id = fwd_from.from_id

        if isinstance(from_id, PeerChannel):
            id_value = from_id.channel_id
            fwd_from_chats.append(id_value)

        elif isinstance(from_id, PeerChat):
            id_value = from_id.chat_id
            fwd_from_chats.append(id_value)

    return fwd_from_chats


def get_mentioned_chats(mentioned_chats, message):
    """
    Extracts mentioned chats from the message text.
    It looks for mentions in the format '@chat_username' and 't.me/chat_username' and adds them
    to the specified dictionary of mentioned chats.

    Parameters:
    - mentioned_chats (dict): A dictionary containing lists for mentions with '@' and 't.me'.
    - message (Message): The Telegram message object.

    Returns:
    dict: An updated dictionary of mentioned chats.

    Note:
    More about message object: https://core.telegram.org/type/Message.

    """
    message_text = message.message
    if message_text:
        mention = re.findall(r"(?:(?:https?://)?t\.me/|t\.me/)(\w+)", message_text)
        mentioned_chats["mentions_with_tdotme"].extend(mention)
        mention = re.findall(r"@(\w+)", message_text)
        mentioned_chats["mentions_with_at"].extend(mention)

    return mentioned_chats


async def get_messages(client, chat, messages_collection):
    """
    Retrieves messages from a Telegram chat and stores them in a MongoDB collection.

    This asynchronous function retrieves messages from the specified Telegram chat using the
    Telegram client. It iteratively fetches messages in batches, processes forwarded chats
    and mentioned chats, and stores the message data in the provided MongoDB 'messages_collection'.

    Parameters:
    - client (TelegramClient): The Telegram client.
    - chat: The chat entity for which to retrieve messages (chat_id or entity object).
    - messages_collection: The MongoDB collection where the message information will be stored.

    Returns:
    tuple: A tuple containing dictionaries of mentioned chats and forwarded chat IDs.

    Note:
    More about message object: https://core.telegram.org/type/Message.
    """
    limit = 100
    total_count_limit = 0
    offset_id = 0
    all_messages = []
    total_messages = 0
    mention_with_tdotme_full = []
    mention_with_at_full = []
    fwd_from_chats_full = []
    mentioned_chats = {
        "mentions_with_tdotme": mention_with_tdotme_full,
        "mentions_with_at": mention_with_at_full,
    }

    while True:
        print(
            "ID of the last collected message:",
            offset_id,
            "; Total collected messages:",
            total_messages,
        )
        history = await client(
            GetHistoryRequest(
                peer=chat,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0,
            )
        )

        if not history.messages:
            break

        messages = history.messages
        for message in messages:
            total_messages += 1
            # Getting fwd from chats
            fwd_from_chats = get_fwd_from(message)
            fwd_from_chats_full.extend(fwd_from_chats)
            # Getting mentioned chats
            mentioned_chats = get_mentioned_chats(mentioned_chats, message)

            all_messages.append(message.to_dict())

        offset_id = messages[len(messages) - 1].id

        if total_count_limit != 0 and total_messages >= total_count_limit:
            break

    await write_data(all_messages, messages_collection)

    return mentioned_chats, fwd_from_chats_full


async def main_get_messages_mentions(
    iteration_num,
    chat_id,
    linked_chat_id,
    client,
    messages_collection,
    network_collection,
):
    """
    Main function to retrieve and process messages from a Telegram chat.

    This asynchronous function serves as the main entry point for retrieving and processing messages
    from a Telegram chat. It calls the `get_messages` function to retrieve messages and associated
    information, creates a dictionary containing mentioned chats, forwarded chats, and other details,
    and inserts the dictionary into the specified MongoDB 'network_collection'.

    Parameters:
    - iteration_num: The iteration number associated with the processed data.
    - chat_id: The chat ID for which to retrieve and process messages.
    - linked_chat_id: The ID of a linked chat (found in the object retrived from
    modules.main_crawler.get_chat_info().
    - client (TelegramClient): The Telegram client.
    - messages_collection: The MongoDB collection where the message information will be stored.
    - network_collection: The MongoDB collection where the network information will be stored.

    Returns:
    None
    """
    try:
        mentioned_chats, fwd_from_chats_full = await get_messages(
            client, chat_id, messages_collection
        )

        # Creating chat dictionary with mentioned chats
        all_mentions_dict = {}
        all_mentions_dict = {
            "iteration_num": iteration_num,
            "chat_id": chat_id,
            **mentioned_chats,
            "fwd_from": fwd_from_chats_full,
            "linked": linked_chat_id,
        }
        network_collection.insert_one(all_mentions_dict)

    except Exception as e:
        logging.error(
            f"An error occurred in get_messages for chat (or it was writing response to the file) {chat_id}: {str(e)}"
        )


async def main_get_participants(chat_id, client, participants_collection):
    """
    Main function to retrieve and process participants of a Telegram chat.

    Parameters:
    - chat_id: The chat ID for which to retrieve and process participants.
    - client (TelegramClient): The Telegram client.
    - participants_collection: The MongoDB collection where the participant information will be stored.

    Returns:
    None
    """
    try:
        await get_participants(client, chat_id, participants_collection)

    except Exception as e:
        # Check if the error message indicates that admin privileges are required
        error_message = str(e)
        if "Chat admin privileges are required to do that" not in error_message:
            # Log the error if it's not the specific excluded error
            logging.error(
                f"An error occurred in get_participants for chat {chat_id}: {error_message}"
            )
