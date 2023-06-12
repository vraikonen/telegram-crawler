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



