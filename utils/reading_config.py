import configparser
import os

# Config file location
# config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'config-bastiaugen.ini')

def reading_config(config_file):
    # Reading Configs
    config = configparser.ConfigParser()
    config.read(config_file)

    # Setting configuration values
    api_id = config['Telegram']['api_id']
    api_hash = config['Telegram']['api_hash']
    api_hash = str(api_hash)

    phone = config['Telegram']['phone']
    username = config['Telegram']['username']

    # Reading number of iterations
    num_levels = config.get('Telegram', 'num_levels')
    num_levels = int(num_levels)

    return api_id, api_hash, phone, username, num_levels


def reading_config_database(config_file):
    # Reading Configs
    config = configparser.ConfigParser()
    config.read(config_file)

    # Setting configuration values
    server_path = config['Database']['server_path']
    print(server_path)
    database = config['Database']['database']
    collection1 = config['Database']['collection1']
    collection2 = config['Database']['collection2']
    collection3 = config['Database']['collection3']
    collection4 = config['Database']['collection4']


    return server_path, database, collection1, collection2, collection3, collection4



# # Define path to the server
# server_path = "mongodb://localhost:27017/"

# # Define the database name
# database = "Telegram-5-crawler"

# # Create the collections
# collection1 = "chats"
# collection2 = "messages"
# collection3 = "network"
# collection4 = "participants