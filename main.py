import json
import asyncio
import re
import urllib.parse
import time
from datetime import datetime
import logging

from telethon import errors # check this later to see if you could use it to handle specific exceptions
from telethon import TelegramClient
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.functions.channels import (
    GetFullChannelRequest, GetParticipantsRequest)
from telethon.tl.types import (
    PeerChannel, ChannelParticipantsSearch)
from telethon.tl import functions, types


from utils.reading_config import reading_config
from utils.authorization_check import authorize_client
from modules.saving_netowork import DateTimeEncoder
from modules.saving_netowork import save_level_data
from modules.saving_netowork import read_channels_from_file


logging.basicConfig(
    filename='applicationMain.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        return super().default(obj)
    
# Reading Configs
config_file = 'config/config-bastiaugen.ini'
api_id, api_hash, phone, username, num_levels = reading_config(config_file)

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)

# First connection to the chat
async def get_entity(entity):
    if entity.isdigit():
        entity = PeerChannel(int(entity))
    else:
        entity = entity
    current_chat = await client.get_entity(entity)
    return current_chat

# Getting further information about the chat
async def get_chat_info(client, current_chat):
    # chat_info = []

    chat_full = await client(GetFullChannelRequest(current_chat))
    #print(chat_full.stringify())
    chat_dict = chat_full.to_dict()
    #print(chat_dict)
    #chat_info.append(chat_dict)
    #print(chat_info)
    
    return chat_dict

async def get_participants(chat):
    limit=100
    offset = 0
    all_participants = []

    while True:
        participants = await client(GetParticipantsRequest(
            chat, ChannelParticipantsSearch(''), offset, limit, hash=0
        ))
        if not participants.users:
            break
        all_participants.extend(participants.users)
        offset += len(participants.users)

    all_user_details = []
    for participant in all_participants:
        all_user_details.append(participant.to_dict())

    all_users_by_chat = {}
    all_users_by_chat[chat] = all_user_details
    
    return all_users_by_chat


async def get_messages(chat):

    limit=100
    total_count_limit=0
    offset_id = 0
    all_messages = []
    filtered_messages = []
    total_messages = 0
    mentioned_chats = []
    fwd_chats = []
    
    while True:
        #print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
        history = await client(GetHistoryRequest(
            peer=chat,
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
            all_messages.append(message.to_dict())

            # Include "fwd_from" channel ID if available
            fwd_from = message.fwd_from
            
            if fwd_from and isinstance(fwd_from, dict):
                from_id = fwd_from.get("from_id", {})
                if from_id and isinstance(from_id, dict):
                    if "channel_id" in from_id:
                        id_value = from_id["channel_id"]
                    elif "chat_id" in from_id:
                        id_value = from_id["chat_id"]

                    #print("ID value:", id_value)
                    fwd_chats.append(id_value)
                    #print(f"FWD: {fwd_chats}")


            # Getting mentioned chats
            if message.message and "https://t.me/" in message.message:
                words = message.message.split()
                filtered_words = [word for word in words if word.startswith("https://t.me/")]
                for url in filtered_words:
                    chat_name = urllib.parse.urlparse(url).path.split('/')[1]
                    mentioned_chats.append(chat_name)
                    #print(f"MNT: {mentioned_chats}")
        
        offset_id = messages[len(messages) - 1].id
        total_messages = len(all_messages)
        
        if total_count_limit != 0 and total_messages >= total_count_limit:
            break
    
    return all_messages, mentioned_chats, fwd_chats

# Write to json
def append_data_to_json(data, filename):
    with open(filename, 'a') as file:
        file.write('\n')  # Add a new line before appending new data
        json.dump(data, file, indent=None, cls=CustomEncoder)

async def main(phone):
    async with client:
        await client.start()
        logging.info("Client Created")

        # Authorize cient if needed
        me = await authorize_client(client, phone)

        # Reading chats from a text file
        entities = read_channels_from_file('input_chats.txt')

        # Initialize a set for processed chats
        processed_chats = set()
        # Initialize dictionary containing chat network
        full_iteration = {}
        # Initialize iteration number
        iteration_num = 1
        
        duration_minutes = 400 # Set the duration
        end_time = time.time() + duration_minutes * 60
        # iteration_limit = 300  # Set the iteration limit to 300 which is approximately one day
        
        while time.time() < end_time:
        
            # Main code: Iterating over input/mentioned chats
            for entity in entities:
                
                # Creating first connection with the chat
                try:
                    current_chat = await get_entity(entity)
                    logging.info(f"Current processing chat is: {current_chat.id}")
                except Exception as e:
                    logging.error(f"An error occurred for get_entity {entity}: {str(e)}")
                    continue
                
                # Skipping proccessed entities before get_chat_info() because it produces rate limits
                if current_chat.id in processed_chats:
                    logging.info(f"Chat {current_chat.id} has already been processed. Skipping...")
                    continue
                
                # Getting chat info and writing it 
                try:
                    chat_info = await get_chat_info(client, current_chat)
                    append_data_to_json(chat_info, 'chat_info.json')
                except Exception as e:
                    logging.error(f"An error occurred for get_chat_info {current_chat}: {str(e)}")
                    continue

                # Getting chat_id from chat_info used in data retrieval
                chat_id = chat_info['full_chat']['id']
                print(chat_id)        
                # Linked_chat_id is always a group linked to a channel or vice versa
                linked_chat_id = chat_info['full_chat']['linked_chat_id']
                print(f"LNK: {linked_chat_id}")
                
                # Apply functions for fetching data
                try:
                    messages, mentioned_chats, fwd_chats = await get_messages(chat_id)
                    append_data_to_json(messages, 'messages.json')
                    success = True
                except Exception as e:
                    logging.error(f"An error occurred in get_messages for chat (or it was writing response to the file) {chat_id}: {str(e)}")
                    success = False
                try:
                    participants = await get_participants(chat_id)
                    append_data_to_json(participants, 'participants.json')
                    success = True
                except Exception as e:
                    logging.error(f"An error occurred in get_participants for chat (or it was writing response to the file) {chat_id}: {str(e)}")
                    success = False

                # Check if either of the try blocks was successful (maybe there is chance that sometimes we could get participants but not messages for some reason)
                if not success:
                    continue 

                # Adding processed chat
                processed_chats.add(chat_id)

                # Combining all mentioned chats
                all_mentions = mentioned_chats + fwd_chats
                if linked_chat_id is not None:
                    all_mentions.append(linked_chat_id)
                #print(all_mentions)
                all_mentions_dict = {chat_id: all_mentions}
                #print(all_mentions_dict)

                # Combining all proccesed chats and their mentions
                full_iteration.setdefault(f"iteration{iteration_num}", []).append(all_mentions_dict)
                #logging.info(full_iteration)
            append_data_to_json(full_iteration, 'chat_network.json')

            # Logic for new iteration:
            iteration_num += 1
            entities = all_mentions
            logging.info(f"Chats proccessed in a previous iterations {processed_chats}")
            #logging.info(full_iteration)

with client:
    client.loop.run_until_complete(main(phone))