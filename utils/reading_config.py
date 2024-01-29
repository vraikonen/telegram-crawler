import configparser
import os
from telethon import TelegramClient


def reading_config(username):
    """
    Reads configuration values from a Telegram config file.

    Parameters:
    - username (str): Gathered from parsing config-tg-{username}.ini
    in utils.reading_config.initialize_clients()

    Returns:
    tuple: A tuple containing the following configuration values:
        - api_id (str): The Telegram API ID.
        - api_hash (str): The Telegram API hash.
        - phone (str): The Telegram phone number.
    """
    # Reading Configs
    config = configparser.ConfigParser()
    config.read(f"config/config-tg-{username}.ini")

    # Setting configuration values
    api_id = config["Telegram"]["api_id"]
    api_hash = config["Telegram"]["api_hash"]
    api_hash = str(api_hash)

    phone = config["Telegram"]["phone"]

    return api_id, api_hash, phone


def reading_config_database(config_file):
    """
    Reads database configuration values from a database config
    file and two scrpt related variables.

    Parameters:
    - config_file (str): The path to the database config file.

    Returns:
    tuple: A tuple containing the following configuration values:
        - server_path (str): The server path for the database.
        - database (str): The name of the database.
        - collection1 (str): Name of the first collection.
        - collection2 (str): Name of the second collection.
        - collection3 (str): Name of the third collection.
        - collection4 (str): Name of the fourth collection.
        - collection5 (str): Name of the fifth collection.
        - max_run_time (str): Maximum run time configuration.
        - max_iterations (str): Maximum iterations configuration.
    """
    # Reading Configs
    config = configparser.ConfigParser()
    config.read(config_file)

    # Setting configuration values
    server_path = config["Database"]["server_path"]

    database = config["Database"]["database"]

    collection1 = config["Database"]["collection1"]
    collection2 = config["Database"]["collection2"]
    collection3 = config["Database"]["collection3"]
    collection4 = config["Database"]["collection4"]
    collection5 = config["Database"]["collection5"]
    max_run_time = config["Database"]["max_run_time"]

    max_iterations = config["Database"]["max_iterations"]

    return (
        server_path,
        database,
        collection1,
        collection2,
        collection3,
        collection4,
        collection5,
        max_run_time,
        max_iterations,
    )


def initialize_clients(folder_path="config"):
    """
    Initializes Telegram client objects based on configuration files.

    Parameters:
    - folder_path (str, optional): The path to the folder containing configuration files.
                                   Defaults to "config".

    Returns:
    tuple: A tuple containing:
        - list: A list of initialized Telegram clients.
        - dict: A dictionary mapping each client to a list containing:
                - str: The phone number associated with the client.
                - str: The username associated with the client.
                - str: The initial connection status of the client.
    """
    clients = []
    client_details = {}

    # List all files in the specified folder
    config_files = [
        f
        for f in os.listdir(folder_path)
        if f.startswith("config-tg-") and f.endswith(".ini")
    ]

    for config_file in config_files:
        # Extract username from the filename
        username = config_file[len("config-tg-") : -len(".ini")]

        # Create separate path for session files
        session_path = f"sessions/{username}"
        os.makedirs(session_path, exist_ok=True)
        session_path = f"sessions/{username}/{username}.session"

        api_id, api_hash, phone = reading_config(username)

        client = TelegramClient(session_path, api_id, api_hash)
        clients.append(client)
        client_details[client] = [phone, username, "Connection status"]

    return clients, client_details
