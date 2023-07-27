import json
import asyncio
import re
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
from modules.saving_netowork import read_channels_from_file
from modules.main_crawler import (
    get_entity, get_chat_info, get_participants, get_fwd_from, get_mentioned_chats, get_messages)

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

# # First connection to the chat
# async def get_entity(entity):
#     if str(entity).isdigit():
#         entity = PeerChannel(int(entity))
#     else:
#         entity = entity
#     current_chat = await client.get_entity(entity)
#     return current_chat

# # Getting further information about the chat
# async def get_chat_info(client, current_chat):
#     # chat_info = []

#     chat_full = await client(GetFullChannelRequest(current_chat))
#     chat_dict = chat_full.to_dict()
    
#     return chat_dict

# async def get_participants(chat):
#     limit=100
#     offset = 0
#     all_participants = []

#     while True:
#         participants = await client(GetParticipantsRequest(
#             chat, ChannelParticipantsSearch(''), offset, limit, hash=0
#         ))
#         if not participants.users:
#             break
#         all_participants.extend(participants.users)
#         offset += len(participants.users)

#     all_user_details = []
#     for participant in all_participants:
#         all_user_details.append(participant.to_dict())

#     all_users_by_chat = {}
#     all_users_by_chat[chat] = all_user_details
    
#     return all_users_by_chat


# def get_fwd_from(message):
#     fwd_from_chats = []

#     fwd_from = message.fwd_from
#     if fwd_from and isinstance(fwd_from, MessageFwdHeader):
#         from_id = fwd_from.from_id

#         if isinstance(from_id, PeerChannel):
#             id_value = from_id.channel_id
#             fwd_from_chats.append(id_value)

#         elif isinstance(from_id, PeerChat):
#             id_value = from_id.chat_id
#             fwd_from_chats.append(id_value)

#     return fwd_from_chats

# def get_mentioned_chats(message):
#     mentioned_chats = []

#     message_text = message.message
#     if message_text:
#         # Using regular expressions to find both URLs and @channel_username mentions
#         mentions = re.findall(r"(?:(?:https?://)?t\.me/|@)(\w+)", message_text)
#         for mention in mentions:
#             mentioned_chats.append(mention)

#     return mentioned_chats

# async def get_messages(chat):

#     limit=100
#     total_count_limit=0
#     offset_id = 0
#     all_messages = []
#     total_messages = 0
#     mentioned_chats_full = []
#     fwd_from_chats_full = []
#     while True:
#         #print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
#         history = await client(GetHistoryRequest(
#             peer=chat,
#             offset_id=offset_id,
#             offset_date=None,
#             add_offset=0,
#             limit=limit,
#             max_id=0,
#             min_id=0,
#             hash=0
#         ))
        
#         if not history.messages:
#             break
        
#         messages = history.messages
#         for message in messages:
#             all_messages.append(message.to_dict())

#             # Getting fwd from chats
#             fwd_from_chats = get_fwd_from(message)
#             fwd_from_chats_full.extend(fwd_from_chats)


#             # Getting mentioned chats
#             mentioned_chats = get_mentioned_chats(message)
#             mentioned_chats_full.extend(mentioned_chats)
        
#         offset_id = messages[len(messages) - 1].id
#         total_messages = len(all_messages)
        
#         if total_count_limit != 0 and total_messages >= total_count_limit:
#             break

#     return all_messages, mentioned_chats_full, fwd_from_chats_full

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

        # Initialize a set for processed chats/how large can this be knowing it will stay in the memory
        processed_chats = set()

        # Define variables for get_entity() exceptions for request to be awaited
        max_delay_time = 60
        delay_multiplier = 5
        consecutive_errors = 0
        
        # Initialize iteration number, define iteration time
        iteration_num = 1
        duration_minutes = 240 # Set the duration
        end_time = time.time() + duration_minutes * 60

        while time.time() < end_time:

            # Define full_iteration dictionary which will be overwritten with each new full iteration (iteration over all input chats),
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
                    logging.error(f"An error occurred for get_entity {entity}: {str(e)}")
                    # Calculate the delay time based on the consecutive error count
                    delay_time = min(max_delay_time, (consecutive_errors + 1) * delay_multiplier)
                    print(delay_time)
                    consecutive_errors += 1
                    await asyncio.sleep(delay_time)
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
                

                ### CHECK THIS SECTION WHEN YOU LATER WANT TO SAVE CHAT INFO DIFFERENTELY
                # Getting chat_id from chat_info used in data retrieval; linked_chat_id is always a group linked to a channel or vice versa
                chat_id = chat_info['full_chat']['id']        
                linked_chat_id = chat_info['full_chat']['linked_chat_id']

                # Apply functions for fetching data
                try:
                    messages, mentioned_chats_full, fwd_from_chats_full = await get_messages(client, chat_id)
                    print(messages)
                    print(mentioned_chats_full)
                    print(fwd_from_chats_full)
                    append_data_to_json(messages, 'messages.json')

                    # Creating chat dictionary with mentioned chats
                    all_mentions_dict = {}
                    all_mentions_dict[chat_id] = {
                        "Mentioned": mentioned_chats_full,
                        "Fwd_from": fwd_from_chats_full,
                        "Linked": linked_chat_id,
                    }
                    
                    # Appending chat dictionary with mentioned chats to all chat dictionaries with mentioned chats from this iteration
                    full_iteration.setdefault(f"iteration{iteration_num}", []).append(all_mentions_dict)
                
                except Exception as e:
                    logging.error(f"An error occurred in get_messages for chat (or it was writing response to the file) {chat_id}: {str(e)}")

                try:
                    participants = await get_participants(client, chat_id)
                    append_data_to_json(participants, 'participants.json')
                    print(participants)
                    # success = True
                except Exception as e:
                    # Check if the error message indicates that admin privileges are required
                    error_message = str(e)
                    if "Chat admin privileges are required to do that" not in error_message:
                        # Log the error if it's not the specific excluded error
                        logging.error(f"An error occurred in get_participants for chat {chat_id}: {error_message}")
                
                # Add chat id to the processed chats
                processed_chats.add(chat_id)
                # Append the values of all mentioned chat types
                all_mentions.extend(mentioned_chats_full)
                all_mentions.extend(fwd_from_chats_full)
                if linked_chat_id is not None: 
                    all_mentions.append(linked_chat_id)
                print(all_mentions)
           
            # Save full iteration
            append_data_to_json(full_iteration, 'full_iteration.json')
            
            # Define next full iteration entities
            next_iteration = set(all_mentions)
            next_iteration_list = list(next_iteration)
            entities = next_iteration_list

            # Itertion number for the next full iteration is +1
            iteration_num += 1   
         
with client:
    client.loop.run_until_complete(main(phone))


