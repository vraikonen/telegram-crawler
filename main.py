import asyncio
import time
import logging

from telethon import errors # check this later to see if you could use it to handle specific exceptions
from telethon import TelegramClient
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.functions.channels import (
    GetFullChannelRequest, GetParticipantsRequest)
from telethon.tl.types import (
    PeerChannel, PeerChat, MessageFwdHeader, ChannelParticipantsSearch)
from telethon.tl import functions, types


from utils.reading_config import (reading_config,reading_config_database)
from utils.authorization_check import authorize_client
from modules.saving_netowork import read_channels_from_file
from modules.main_crawler import (
    get_entity, get_chat_info, get_participants, get_messages, initialize_mongodb)


logging.basicConfig(
    filename='applicationMain.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)

# Reading Configs
config_telegram = 'config/config-bastiaugen.ini'
api_id, api_hash, phone, username, num_levels = reading_config(config_telegram)

config_database = 'config/config-database.ini'
server_path, database, collection1, collection2, collection3, collection4 = reading_config_database(config_database)

# Connect to database and create table and collections
chats_collection, messages_collection, network_collection, participants_collection = initialize_mongodb(
    server_path, database, collection1, collection2, collection3, collection4)

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)

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
        duration_minutes = 1000 # Set the duration
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
                    consecutive_errors += 1
                    await asyncio.sleep(delay_time)
                    continue
                
                # Skipping proccessed entities before get_chat_info() because it produces rate limits
                if current_chat.id in processed_chats:
                    logging.info(f"Chat {current_chat.id} has already been processed. Skipping...")
                    continue

                try:
                    chat_info = await get_chat_info(client, current_chat, chats_collection)
                    #append_data_to_json(chat_info, 'chat_info.json')
                except Exception as e:
                    logging.error(f"An error occurred for get_chat_info {current_chat}: {str(e)}")
                    continue
                

                ### CHECK THIS SECTION WHEN YOU LATER WANT TO SAVE CHAT INFO DIFFERENTELY
                # Getting chat_id from chat_info used in data retrieval; linked_chat_id is always a group linked to a channel or vice versa
                chat_id = chat_info['full_chat']['id']        
                linked_chat_id = chat_info['full_chat']['linked_chat_id']

                # Apply functions for fetching data
                try:
                    mentioned_chats_full, fwd_from_chats_full = await get_messages(client, chat_id, messages_collection)

                    # Creating chat dictionary with mentioned chats
                    all_mentions_dict = {}
                    all_mentions_dict[str(chat_id)] = {
                        "Mentioned": mentioned_chats_full,
                        "Fwd_from": fwd_from_chats_full,
                        "Linked": linked_chat_id,
                    }
                    
                    # Appending chat dictionary with mentioned chats to all chat dictionaries with mentioned chats from this iteration
                    full_iteration.setdefault(f"iteration{iteration_num}", []).append(all_mentions_dict)
                    print(full_iteration)
                
                except Exception as e:
                    logging.error(f"An error occurred in get_messages for chat (or it was writing response to the file) {chat_id}: {str(e)}")

                try:
                    await get_participants(client, chat_id, participants_collection)

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

            network_collection.insert_one(full_iteration)
            
            # Define next full iteration entities
            next_iteration = set(all_mentions)
            next_iteration_list = list(next_iteration)
            entities = next_iteration_list

            # Itertion number for the next full iteration is +1
            iteration_num += 1   
         
with client:
    client.loop.run_until_complete(main(phone))



