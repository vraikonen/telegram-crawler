from telethon.errors import SessionPasswordNeededError


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
