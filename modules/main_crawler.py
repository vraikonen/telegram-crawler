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
    server_path, database, collection1, collection2, collection3, collection4
):
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

    # Return the collections
    return collection1, collection2, collection3, collection4


# Writing in the database
def write_data(data, collection_name):
    try:
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
    try:
        collection.create_index(index, unique=False)
    except Exception as e:
        logging.error(f"Error creating index in {collection}: {str(e)}")


# First connection to the chat
async def get_entity(client, entity):
    if str(entity).isdigit():
        entity = PeerChannel(int(entity))
    else:
        entity = entity
    current_chat = await client.get_entity(entity)
    return current_chat


# Getting further information about the chat
async def get_chat_info(client, current_chat, chats_collection):
    chat_full = await client(GetFullChannelRequest(current_chat))
    chat_dict = chat_full.to_dict()
    write_data(chat_dict, chats_collection)
    return chat_dict


async def get_participants(client, chat, participants_collection):
    limit = 100
    offset = 0
    all_participants = []

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
            # Insert each participant as it is retrieved
            write_data(participant_data, participants_collection)
        offset += len(participants.users)


def get_fwd_from(message):
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


def get_mentioned_chats(message):
    mentioned_chats = []

    message_text = message.message
    if message_text:
        # Using regular expressions to find both URLs and @channel_username mentions
        mentions = re.findall(r"(?:(?:https?://)?t\.me/|@)(\w+)", message_text)
        for mention in mentions:
            mentioned_chats.append(mention)

    return mentioned_chats


async def get_messages(client, chat, messages_collection):
    limit = 100
    total_count_limit = 0
    offset_id = 0
    all_messages = []
    total_messages = 0
    mentioned_chats_full = []
    fwd_from_chats_full = []
    while True:
        print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
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

            write_data(message.to_dict(), messages_collection)
            # Getting fwd from chats
            fwd_from_chats = get_fwd_from(message)
            fwd_from_chats_full.extend(fwd_from_chats)

            # Getting mentioned chats
            mentioned_chats = get_mentioned_chats(message)
            mentioned_chats_full.extend(mentioned_chats)

        offset_id = messages[len(messages) - 1].id
        # total_messages = len(all_messages)

        if total_count_limit != 0 and total_messages >= total_count_limit:
            break

    return mentioned_chats_full, fwd_from_chats_full


async def main_get_messages(iteration_num, full_iteration, chat_id, linked_chat_id, client, messages_collection):
    try:
        mentioned_chats_full, fwd_from_chats_full = await get_messages(
                        client, chat_id, messages_collection
                    )

                    # Creating chat dictionary with mentioned chats
        all_mentions_dict = {}
        all_mentions_dict[str(chat_id)] = {
                        "Mentioned": mentioned_chats_full,
                        "Fwd_from": fwd_from_chats_full,
                        "Linked": linked_chat_id,
                    }

                    # Appending chat dictionary with mentioned chats to all chat 
                    # dictionaries with mentioned chats from this iteration
        full_iteration.setdefault(f"iteration{iteration_num}", []).append(
                        all_mentions_dict
                    )

    except Exception as e:
        logging.error(
                        f"An error occurred in get_messages for chat (or it was writing response to the file) {chat_id}: {str(e)}"
                    )
        
    return mentioned_chats_full,fwd_from_chats_full


async def main_get_participants(chat_id,client,participants_collection):
    try:
        await get_participants(client, chat_id, participants_collection)

    except Exception as e:
                    # Check if the error message indicates that admin privileges are required
        error_message = str(e)
        if (
                        "Chat admin privileges are required to do that"
                        not in error_message
                    ):
                        # Log the error if it's not the specific excluded error
            logging.error(
                            f"An error occurred in get_participants for chat {chat_id}: {error_message}"
                        )