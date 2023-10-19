<a name="readme-top"></a>


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://git.sbg.ac.at/geo-social-analytics/geo-social-media/telegram-crawler">
    <img src="img/icon.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">Main Telegram Crawler</h3>

  <p align="center">
    This is a Python script that utilizes the Telethon library to process chats in Telegram. It fetches information about the chats, such as chat details, participants, messages, and chat network, and saves the data to JSON files for further analysis.
    <br />
    <a href="https://git.sbg.ac.at/geo-social-analytics/geo-social-media/telegram-crawler"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://git.sbg.ac.at/geo-social-analytics/geo-social-media/telegram-crawler">View Demo</a>
    ·
    <a href="https://git.sbg.ac.at/geo-social-analytics/geo-social-media/telegram-crawler/-/issues">Report Bug</a>
    ·
    <a href="https://git.sbg.ac.at/geo-social-analytics/geo-social-media/telegram-crawler/-/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#obtaining-credentials-for-telegram-api">Obtaining Credentials for Telegram API</a></li>
	<li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li>
	<a href="#code-explanation">Code Explanation</a>
    	<ul>
         <li><a href="#general-overview">General Overview</a></li>
         <li><a href="#telegram-server-connection">Telegram Server Connection</a></li>
	 <li><a href="#fetching-data">Fetching Data</a></li>
	 <li><a href="#saving-data">Saving Data</a></li>
	</ul>
    </li>
    <li><a href="#class-diagram">Class Diagram</a></li>
    <li><a href="#problems/questions/doubts">Problems/Questions/Doubts</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project
Key Features:
- Currently script fetches information regarding the chat info, messages, participants and chat network and saves it in a json.

Next Steps:
- Testing
- Decide on database and data modeling
- Provide chat update information


<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Telethon](img/telethonimg.png)](https://docs.telethon.dev/en/stable/) Telethon
* [![MongoDB](img/mongo.png)](https://www.mongodb.com/) MongoDB
* [![Python](img/pythonimg.png)](https://www.python.org/) Python

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

### Obtaining Credentials for Telegram API

To access the Telegram API and use it in this project, you need to obtain API credentials. Follow the steps below to obtain the necessary credentials:

1. Visit the [Telegram API Documentation](https://core.telegram.org/api/obtaining_api_id) page.

2. Log in to your Telegram account or create a new account if you don't have one - phone number is required for creating account an obtaining credentials. Further access to the Telegram application is a prerequisite for connection to the server, as authorization code will be sent to your Telegram account as a message.  

3. Go to the [API Development Tools](https://my.telegram.org/auth) page on the Telegram website.

4. Fill in the required information.

5. Once you've provided the required details, you will receive your **API ID** and **API Hash**.

6. Update **config file** with API ID, API Hash, username and phone number.

### Prerequisites
* Telethon library (probably the newest version will also work perfectly fine)
  ```sh
  pip install telethon==1.25.2
  ```
* Python 3.x

### Database connection/roles etc...

### Installation

1. Clone the repo
   ```sh
   git clone 
   ```
2. Install telethon,(add other) packages
   ```sh
   install
   ```
3. Enter api details
   ```sh
   
   ```
4. Enter database connection details

5. Write input chats in text file, each on a new line.

6. Run the script

7. Upon running the script for the first time, an authorization check will be sent to your Telegram account in the form of a message. You will be prompted in the terminal to input the code provided.
<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- Code explanation -->
## Code Explanation

### General Overview
User defines input chats. Script iterates over input chats and fetches messages of a channel and messages and participants of a group, as well as the chat info of both. There is no direct diferentiation between those categories. When a channel is used as an input parameter for participants, it raise an exception and log it to .log file. Script also produces mentioned chats assigned to each of the input chats. Mentioned chats can be found as the chat from which the message has been forwarded, from linked chat endpoint of messages, and through parsing actual messages in order to find the links to other chats. After all input chats have been processed, chats that are mentioned in the input chats become input chats for the next iteration. This continues as long as the time is set in the while loop. One chat will not be accessed twice. Each full iteration (iteration over all input chats or all chats that are found in the previous iteration) produces a nested dictionary that has iteration number and each input chat with associated mentioned chats - a chat network. 
### Telegram Server Connection

### Fetching Data
1. Function `read_channels_from_file()` takes text file `input_chats.txt` as an argument. It loads chats used in the first iteration of data retrival. There is no other way of accessing Telegram chats without providing their username/chat id.
- input_chats.txt is the document with chat usernames, each chat username is on the new line
- current questionable information from the internet: there is no possibility of using chat id if the crawler (Telegram account that uses API) has never encountered that chat before. This is not true, but if this really happens sometimes, there will be no problem if the input chats are usernames, because chats used in second iteration will be encountered during the first one, thus this error will never be raised. After the first connection, an access_hash is created for each chat and it will remain the same until the end of the session.
- difference between username and chat id: users refer to another chat based on a username; chat_id can be obtained only through API; chat_id is used to retrieve messages as it produces less rate limit hits; regardless of the input_chats.txt (where you can put username or chat id), chat id will be used to retrieve messages;
	- **chat id stays the same** regardless of the username/privacy change which is frequent behaviour of the administrators; but there is a chance that one channel will not be accessibile via its id if it becomes private (although there is an option to join private channel and reterive messages); 
	- however!!! if a group is migrated to supergroup or megagroup, id will be changed, nevertheless, there is an option to track this change (migrated_chat_id shows previous id of the chat); currently there is only megaroup and gigagroup type of groups, but this migration can be tracked regardless of the Telegram naming convention for different type of chats;
	- however!!! Telegram can decide to update chat ids from time to time;
 
2. Function `get_entity()` is rather simple. It takes chat username provided by `read_channels_from_file()`. It has logic to deal with chats regardless of their type: id or username. Lastly, it returns entity object that will be used in the next function. Entity object returned from this function provides partial information regarding the input chat. Returned object (entity) "include, but is not limited to, usernames, exact titles, IDs, Peer objects, or even entire User, Chat and Channel objects and even phone numbers from people you have in your contact list". Role of this function is to provide initial connection to the chat. Further information: [link](https://docs.telethon.dev/en/stable/concepts/entities.html). 
3.  Next `get_chat_info()` function is applied to gather information about the chat. It takes as a parameter an entity provided by the previous function and returns comprehensive object that describes chat. Returned dictionary is written in the json file - each chat info on the new line. ~~This function also decides wheter the chat is a group or a channel and append json with new key-value pair "chat_type" = "channel/group". This key-value pair is not nested inside the chat_info json.
The logic for this distinction:~~
    ~~- as Telegram changes naming and other conventions regarding the type of groups and channels, for some reason, each now and then, but do not include explanation in their API documentation, I think this part should be rather simple and based on the type of request you can send to a chat_type (getting participants and other info regarding if there is a discussion option or not). I propose to only distinct between groups and channels (currently there are no direct options to distinct between a channel and a group). Here are two options (probably among many), I have implemented the second one:~~
    ~~- if in the chat_info, the value is True for megagroup attribute, then it is group; if it is True for gigagroup and False for megagroup or if it is false for both - it is a channel - documentation is not updated on this topic as they right now officially have groups, supergroups, megagroups, gigagroups and channels with gigagropus and supergroups are having characteristics the same as the channel~~
    ~~- if there is an attribute default_banned_rights=ChatBannedRights - it is a group;
			  - interesting info: even though group is public, chat admin can ban access to participants.~~
- Every chat regardless of their type will be fetched for `get_participants()`. 
- There are several methods to retrieve chat information: all of them return the same endpoints if used without await (endpoints in this case are just like the endpoints retrieved from `get_entity()`).Important: every telethon request if not awaited will produce partial output, meaning not all endpoints can be retrieved:
	- [functions.messages.GetFullChatRequest](https://core.telegram.org/method/messages.getFullChat)(entity) - if awaited works only for individual chats and not for channels and groups (it says on the offical documentation that it works for basic groups, but that category does not exist anymore(or at least my group of 1 participant was not considered basic), all groups can be obtained from GetFullChannel);
	- [functions.users.GetFullUserRequest](https://core.telegram.org/method/users.getFullUser)(entity) - does not work with channels and groups if awaited but with users (personal contacts or similiar);
	- [functions.channels.GetFullChannelRequest](https://core.telegram.org/method/channels.getFullChannel)(entity) - **The one** with most comprenhensive output:
		- Output is nested: full_chat{}, chats[]and users []. These elements also have nested structure. Output is not standardized in a way that it is possible that one chat have multi-nested values for one attribute, and another one has no attributes. For instance, chat without profile photo will have value null for the key photo, and the one with a photo have multiple key-value pairs describing the photo. Here is a [link](https://core.telegram.org/constructor/messages.chatFull). 
4. Function `get_messages()` takes chat id as an input and returns `messages`, `fwd_chats` and `mentioned chats`. fwd_chats are obtained by accessing the `from_id` endpoint which is nested element of `fwd_from` object (if it exists), for each of the messages. `from_id` endpoint represents the chat from which the message is forwared to our currently processed chat. `mentioned_chats` are obtained by parsing the messages in order to find links to other chats. Both will be used in the next iteration as initial entities, as well as linked_chat_id which represent group connected to channel and vice versa (found as endpoint in get_chat_info response). Returned messages are saved in a json file on one line. There are two options for fetching messages:
- [functions.channels.getMessagesRequest](https://core.telegram.org/method/channels.getMessages) - this request is for specific messages, it is neccessary to define the message id we want to get, therefore not usable.
- [functions.messages.getHistoryRequest](https://core.telegram.org/method/messages.getHistory) - **The one** you need! Here is the structure of the response written as json. 
```json
{
"messages": {
 "messages": ["message", "messageEmpty", "messageService"],
 "chat": ["some attributes"],
 "user": ["some attributes"]
},
"messagesSlice": ["some attributes"],
"channelMessages": ["some attributes"],
"messagesNotModified": ["some attributes"]
}
```
- Function `get_messages()` fetches all objects from messages.messages. It means that all three object types are returned in the list `messages` and saved in the same json together (message, messageEmpty, messageService). One message can belong to only one of these object types (contrary to the previous getFullChannelRequest where three (sub)objects are returned for each chat regardless of its type, although with different attributes). Further attributes of messages.messages are nested. Two messages of the same object type will always have same keys in key-value pair attributes, although values can differ. For instance, one message could have media, thus more multi-level key-value pairs(attributes) attached to the key media. 
- There are few parameters that are neccessary for this method: peer, offset_id, offset_date, add_offset, limit, max_id, min_id and hash. It is possible to define which messages are gonna be skipped, which message will be fetched first, how many messages are gonna be fetched in one go, etc. This can be used to track the last scraped message, thus providing information for the function that populate databse with new messages (although i believe there is a better way). Important notice is that many chats have deleted messages thus the last message id does not corresponds to the total messages that can be retrieved.

5. Function `get_participants()` returns list of dictionaries. Each dictionary represent a participant. Input parameter is chat id. This function is only applied to groups. All participants that belongs to one group are saved on one line in json.
There are two Telethon methods to retrieve participants:
- [functions.channels.GetParticipantRequest](https://core.telegram.org/method/channels.getParticipant) - takes one user id as an input, thus provides data for specific user which is not applicable in this project.
- [functions.channels.GetParticipantsRequest](https://core.telegram.org/method/channels.getParticipants) - this method fetches all participants from group. It takes as an input parameter chat(group) id, offset, limit, hash and filter. The [filter](https://core.telegram.org/type/ChannelParticipantsFilter) parameter can be many objects that filter fetched participants based on some criteria such as is the participant bot, fetch only recent participant etc. This method returns objects channelParticipants and channelParticipantsNotModified. channelParticipants object has subobjects count, participants, chats and users. Function `get_participants()` only fetches channelParticipants.users.

6. Function `append_data_to_json()` saves messages, participants and chat info for each chat on a new line in json. If .json file does not exist, it will be created. Function will be soon replaced by a function that writes it in a database.

7. In the meantime, a chat network json object is created after each full iteration (iteration over all input channels/all mentioned channels from previous iteration). It consists of the key which represents iteration number and list of dictionaries. Each dictionary has a key that is processed chat and values that are all mentioned chats, either through messages parsing, forwards or linked chat. Each new iteration is appended to all the previous ones. After each iteration, new full chat network object is appeneded to json file consisting of all previous iterations.

   
### Saving data

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- Rate Limits -->
## Rate Limits


<!-- Class Diagram -->
## Class Diagram



<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- Problems/questions/doubts -->
## Problems/Questions/Doubts
Important questions right now?
- [ ] Add retry decorator and catch flood await error? - yes
- [ ] MongoDB or something else? I think noSQL is good, really check everything at the end, there might be some change in data structure so you want be able to excecute for instance now it is none, but it can be null for linked_chat_id.


TESTING:
- Install pytest-asyncio library
The <username>.session file is essential for the functioning of the Telegram API client. It stores the necessary session information required to establish a connection to the Telegram server. The file is generated when the TelegramClient instance is initialized for the first time and logs in to the Telegram server. However, when running pytest, it becomes challenging to provide the necessary authorization code interactively, as pytest runs non-interactively in the terminal. This leads to a situation where tests are unable to establish a connection to the Telegram server, and the authorization process cannot be completed.
//
To overcome this issue and enable the successful execution of tests, a preliminary script or setup file can be created. This script should include the necessary steps to initialize the TelegramClient and establish a connection to the Telegram server, including providing the required authorization code. Once the client is authenticated successfully and the <username>.session file is generated, the script can call the get_entity function on any entity as a test setup. Once this initial setup script has been run, the session file will be available for future test runs. Subsequent test executions using pytest in the tests/test_main_crawler folder will not require manual authorization, as they will use the existing <username>.session file for a successful connection to the Telegram server.. 


Important questions later?
- [ ] Updating database with new messages - a lot to discuss (or a lot for me to consider) - include ttl period, hash
- [ ] Defining input chats
- [ ] Language of the chats?
- [ ] What to do if script stops working, should we include something more than just retry?
- [ ] Where and how to log errors?
- [ ] Is scraping participants, chat info, messages and chat network enough or should we include more endpoints? For instance we could get data for participants that have left the chat, I would need to check/test this endpoint https://core.telegram.org/type/ChannelParticipant
- [ ] Should we scrape private chats? there is an option for that although it is not acceptable by the terms of service
- [ ] Which endpoints should be saved, how should it be saved - should I modify dictionaries? - show them server response!!! should i save it as a list of dictionaries or as a dictionary? - Check the possibilities of interacting with database. 

Potential upgrades:
- [ ] Generally go and check all possible endpoints! - problem is that many API requests lead to the same endpoints, although they have different parameters - i believe that these requests that are used here are the broadest ones, meaning they do fetch all possible endpoints 
- [ ] Filter messages on the go for some project https://core.telegram.org/method/messages.search / Search specific messages globally https://core.telegram.org/method/messages.searchGlobal - works only within your chats (chats you are member), this request is actually used in iter_messages which is a function from telethon to retrieve specific messages from a chat (compared to getHistoryRequest that can fetch all messages) - generally best option is to use getHistoryRequest as you can better control request, thus control rate limits hits 
- [ ] Get live location history of a certain user messages.getRecentLocations
- [ ] Is this better way to check linked_chat_id https://core.telegram.org/method/channels.getGroupsForDiscussion / no it is not, this information is obtained from linked_chat_id endpoint of getFullChannelRequest
- [ ] https://core.telegram.org/method/stats.getMessagePublicForwards?  it takes message id as a parameter to check if that message has been forwarded - usually this can be restricted by the administrator, but worth checking definitely for network
<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Roadmap -->
## Roadmap (mainly for me)
- [ ] https://core.telegram.org/constructor/channels.channelParticipants check participants.chat to see if there will be all mentioned channels and chats?!
- [ ] CHECK NAMING< HOW TO CALL DIFFERENT SUBOBJECTS FFS - I still call them objects and subobjects 
- [ ] CHECK HASH AND PAGINATION
- [ ] https://core.telegram.org/constructor/messages.messages check here list of chats mentioned in dialogs? is good for network? - dialog is a chat a user is part, therefore no
- [ ] RATE LIMITS - check event handlers ?! More important check if you put it to sleep for 1 sec, will flod wait info get reduced thus it will be faster?
- [ ] Check these infos? 2023-07-18 12:01:25,028 - INFO - Timeout waiting for updates expired 2023-07-18 12:01:25,028 - INFO - Getting difference for account updates
- [ ] Should i maybe put entities retrieved from get_entity and not chat_id to main functions for data fetching?
- there is no option for joining private groups or channels!
   

See the [open issues](https://git.sbg.ac.at/geo-social-analytics/geo-social-media/telegram-crawler/-/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* []() Nefta
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Errors

Server sent a very old message with ID 7257439166484852737, ignoring
Security error while unpacking a received message: Too many messages had to be ignored consecutively
Server sent a very old message with ID 7257439166484854785, ignoring
Security error while unpacking a received message: Too many messages had to be ignored consecutively
Server sent a very old message with ID 7257439206795578369, ignoring
Security error while unpacking a received message: Too many messages had to be ignored consecutively
Server sent a very old message with ID 7257440675391662081, ignoring
Security error while unpacking a received message: Too many messages had to be ignored consecutively
Server sent a very old message with ID 7257440675391684609, ignoring
Security error while unpacking a received message: Too many messages had to be ignored consecutively
Server sent a very old message with ID 7257440675391685633, ignoring
Security error while unpacking a received message: Too many messages had to be ignored consecutively
Server sent a very old message with ID 7257440675391686657, ignoring
Security error while unpacking a received message: Too many messages had to be ignored consecutively
