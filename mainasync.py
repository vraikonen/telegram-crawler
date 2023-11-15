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
    PeerChannel, PeerChat, MessageFwdHeader, ChannelParticipantsSearch)
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
    if str(entity).isdigit():
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


def get_fwd_from(message):
    fwd_from_chats = []

    fwd_from = message.fwd_from
    if fwd_from and isinstance(fwd_from, MessageFwdHeader):
        from_id = fwd_from.from_id

        if isinstance(from_id, PeerChannel):
            id_value = from_id.channel_id
            fwd_from_chats.append(id_value)
            #print(f"FWD: {id_value} (Channel)")

        elif isinstance(from_id, PeerChat):
            id_value = from_id.chat_id
            fwd_from_chats.append(id_value)
            #print(f"FWD: {id_value} (Chat)")

    return fwd_from_chats

def get_mentioned_chats(message):
    mentioned_chats = []

    message_text = message.message
    if message_text and ("https://t.me/" in message_text or "t.me/" in message_text):
        words = message_text.split()
        filtered_words = [word for word in words if word.startswith("https://t.me/") or word.startswith("t.me/")]
        for url in filtered_words:
            chat_name = urllib.parse.urlparse(url).path.split('/')[1]
            mentioned_chats.append(chat_name)
            #print(f"mentioned chats: {mentioned_chats}")
    return mentioned_chats

# def get_mentioned_chats(message):
#     mentioned_chats = []

#     message_text = message.message
#     if message_text:
#         # Using regular expressions to find both URLs and @channel_username mentions
#         mentions = re.findall(r"(?:(?:https?://)?t\.me/|@)(\w+)", message_text)
#         for mention in mentions:
#             mentioned_chats.append(mention)

#     return mentioned_chats


async def get_messages(chat):

    limit=100
    total_count_limit=0
    offset_id = 0
    all_messages = []
    total_messages = 0
    mentioned_chats_full = []
    fwd_from_chats_full = []
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
            #print(message)
            all_messages.append(message.to_dict())

            # Getting fwd from chats
            fwd_from_chats = get_fwd_from(message)
            #print(f"fwd_from_chats: {fwd_from_chats}")
            fwd_from_chats_full.extend(fwd_from_chats)
            #print(f"fwd_from_chats_full: {fwd_from_chats_full}")


            # Getting mentioned chats
            mentioned_chats = get_mentioned_chats(message)
            mentioned_chats_full.extend(mentioned_chats)
            #print(message_text)
        
        offset_id = messages[len(messages) - 1].id
        total_messages = len(all_messages)
        
        if total_count_limit != 0 and total_messages >= total_count_limit:
            break
    

    # print(fwd_from_chats_full)
    return all_messages, mentioned_chats_full, fwd_from_chats_full

# Write to json
def append_data_to_json(data, filename):
    with open(filename, 'a') as file:
        file.write('\n')  # Add a new line before appending new data
        json.dump(data, file, indent=None, cls=CustomEncoder)


# Initialize a set for processed chats
#processed_chats = set()

async def process_entities(entities, iteration_num):

    async def process_entity(entity):
        
        
        chat_id = None
        # Creating first connection with the chat
        try:
            current_chat = await get_entity(entity)
            await asyncio.sleep(1)
            logging.info(f"Current processing chat is: {current_chat.id}")
        except Exception as e:
            logging.error(f"An error occurred for get_entity {entity}: {str(e)}")
            return False
        
        # Skipping processed entities before get_chat_info() because it produces rate limits
        if current_chat.id in processed_chats:
            logging.info(f"Chat {current_chat.id} has already been processed. Skipping...")
            return False
        # Getting chat info and writing it 
        try:
            chat_info = await get_chat_info(client, current_chat)
            await asyncio.sleep(1)
            append_data_to_json(chat_info, 'chat_info.json')
        except Exception as e:
            logging.error(f"An error occurred for get_chat_info {current_chat}: {str(e)}")
        

        try:
            # Linked_chat_id is always a group linked to a channel or vice versa, chat_id is used to retrieve data
            linked_chat_id = chat_info['full_chat']['linked_chat_id']
            chat_id = chat_info['full_chat']['id']
            print(chat_id)
        except Exception as e:
            logging.error(f"taking chat info and linked chat id {chat_id}: {str(e)}")
            return False
        
        if chat_id in processed_chats:
            logging.info(f"Chat {chat_id} has already been processed. Skipping...")
            return False
        # Initialize a flag to track if either try block succeeded, fecthing data
        success = False
        try:
            messages, mentioned_chats_full, fwd_from_chats_full = await get_messages(chat_id)
            append_data_to_json(messages, 'messages.json')
            print(f'1   MNT: {mentioned_chats_full}')
            print(f'2   FWD: {fwd_from_chats_full}')

            all_mentions_dict = {}
            all_mentions_dict[chat_id] = {
                "Mentioned": mentioned_chats_full,
                "Fwd_from": fwd_from_chats_full,
                "Linked": linked_chat_id,
            }
            print(f"5   all_mentions_dict: {all_mentions_dict}")
            
            full_iteration.setdefault(f"iteration{iteration_num}", []).append(all_mentions_dict)
            print(f"7    : full_iteration: {full_iteration}")
            
            success = True
        except Exception as e:
            logging.error(f"An error occurred in get_messages for chat (or it was writing response to the file) {chat_id}: {str(e)}")
        
        try:
            participants = await get_participants(chat_id)
            append_data_to_json(participants, 'participants.json')
        except Exception as e:
            logging.error(f"An error occurred in get_participants for chat (or it was writing response to the file) {chat_id}: {str(e)}")
        
        processed_chats.add(chat_id)
        
    # Gather results from all entities using asyncio
    tasks = [process_entity(entity) for entity in entities]
    results = await asyncio.gather(*tasks)

    # Check if any of the tasks had errors
    if not all(results):
        logging.error("Some tasks failed while processing entities. Exiting...")
        return
    # if not all(results):
    #     logging.error("Some tasks failed while processing entities:")
    #     for index, result in enumerate(results):
    #         if not result:
    #             logging.error(f"Task {index + 1} failed.")
    # Return the full_iteration dictionary
    #return full_iteration


full_iteration = {}
processed_chats = set()
async def main(phone):
    async with client:
        await client.start()
        logging.info("Client Created")

        # Authorize client if needed
        me = await authorize_client(client, phone)
        
        
        iteration_num = 1
        duration_minutes = 1440 # Set the duration
        end_time = time.time() + duration_minutes * 60

        entities = read_channels_from_file('input_nazi.txt')

        while time.time() < end_time:
            all_mentions = []
            next_iteration = set()
            # Run the asyncio loop with the function

            await process_entities(entities, iteration_num)

            if full_iteration is not None:
                print(f"7    : full_iteration: {full_iteration}")
                for iteration, iteration_data in full_iteration.items():
                    # Loop through the nested dictionaries inside each iteration
                    for data_dict in iteration_data:
                        # Loop through the keys and values of each nested dictionary
                        for chat_id, chat_data in data_dict.items():
                            # Extract the mentioned, fwd_from, and linked values from each dictionary
                            mentioned_chats = chat_data['Mentioned']
                            fwd_from_chats = chat_data['Fwd_from']
                            linked_chat = chat_data['Linked']
                            #processed_chats.append(chat_id)

                            # Append the values to the respective lists
                            all_mentions.extend(mentioned_chats)
                            all_mentions.extend(fwd_from_chats)
                            if linked_chat is not None: 
                                all_mentions.append(linked_chat)
            else:
                print("An error occurred while processing entities. Exiting...")
                break
            append_data_to_json(full_iteration, 'full_iteration.json')
            print(f"7    : full_iteration: {full_iteration}")
            print(all_mentions)
            next_iteration = set(all_mentions)


            next_iteration_list = list(next_iteration)
            print(next_iteration_list)
            entities = next_iteration_list
            print(entities)
            print(processed_chats)

            iteration_num += 1

with client:
    client.loop.run_until_complete(main(phone))