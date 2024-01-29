from telethon.errors import SessionPasswordNeededError
import logging


# Check if the user is authorized, otherwise initiate the sign-in proces
async def authorize_client(client, phone):
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input("Enter the code: "))
        except SessionPasswordNeededError:
            await client.sign_in(password=input("Password: "))

    me = await client.get_me()
    return me


# Check Authorization
async def authorize_clients(client, client_details):
    """
    Authorizes a Telegram client using the provided details.

    This asynchronous function attempts to authorize the specified Telegram client using the provided
    details in the 'client_details' dictionary created by function utils.reading_config.initialize_clients().
    It starts the client, sends a code request if the client is not already authorized, and handles
    the authorization process, including handling password input if required.

    Parameters:
    - client (TelegramClient): The Telegram client to be authorized.
    - client_details (dict): A dictionary containing client details, including phone number, username, and
    and initial connection status.

    Returns:
    None
    """
    try:
        print(f"Authorization for: {client_details[client]}")
        async with client:
            await client.start()
            if not await client.is_user_authorized():
                await client.send_code_request(client_details[client][0])
                try:
                    await client.sign_in(
                        client_details[client][0], input("Enter the code: ")
                    )
                except SessionPasswordNeededError:
                    await client.sign_in(password=input("Password: "))

            me = await client.get_me()
            print("Authorization finished. Disconnecting...")
            client.disconnect()
            # me = await authorize_client(client, client_details[client])
    except Exception as e:
        logging.error(f"Error creating client {client_details[client]}: {str(e)}")
