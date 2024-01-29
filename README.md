<a name="readme-top"></a>


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://git.sbg.ac.at/geo-social-analytics/geo-social-media/telegram-crawler">
    <img src="img/icon.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">Main Telegram Crawler</h3>

  <p align="center">
    This is a Python script that utilizes Telethon library to process chats from Telegram. It fetches information about the chats, such as chat details, participants, messages, and chat network, and saves the data to MongoDB database for the further analysis.
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
	<li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#obtaining-credentials-for-telegram-api">Obtaining Credentials for Telegram API</a></li>
	<li><a href="#database-configuration">Database configuration</a></li>
	<li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li>
	<a href="#code-explanation">Code Explanation</a>
    	<ul>
         <li><a href="#general-overview">General Overview</a></li>
         <li><a href="#flowchart">Flowchart</a></li>
	 <li><a href="#class-diagram">Class Diagram</a></li>
	</ul>
    </li>
    <li><a href="#db-data-structure">DB Data Structure</a></li>
    <li><a href="#queries-example-and-tips">Queries example and tips</a></li>
    <li><a href="#problems/questions/doubts">Problems/Questions/Doubts</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project
Key Features:
- The script currently fetches the information regarding the chat info, messages, participants and chat network and saves it in the MongoDB.


### Built With

* [![Telethon](img/telethonimg.png)](https://docs.telethon.dev/en/stable/) Telethon
* [![MongoDB](img/mongo.png)](https://www.mongodb.com/) MongoDB
* [![Python](img/pythonimg.png)](https://www.python.org/) Python



<!-- GETTING STARTED -->
## Getting Started

### Prerequisites
* Python 3.x
* MongoDB Community Server 7.x
* Telethon library
  ```sh
  pip install telethon==1.29.2
  ```
* PyMongo
  ```sh
  pip install pymongo==3.12.0
  ```

### Obtaining Credentials for Telegram API

To access the Telegram API and use it in this project, you need to obtain API credentials. Follow the steps below to obtain the necessary credentials:

1. Visit the [Telegram API Documentation](https://core.telegram.org/api/obtaining_api_id) page.

2. Log in to your Telegram account or create a new account if you don't have one - a phone number is required for creating the account and obtaining the credentials. Further access to the Telegram application is a prerequisite for connection to the server, as authorization code will be sent to your Telegram account as a message.  

3. Go to the [API Development Tools](https://my.telegram.org/auth) page on the Telegram website. Use Edge/Mozilla for this step.

4. Fill in the required information. Do not care about the application name, nevertheless write something meaningful, such as "tgApplicaiton" or "Mycrawler". Try until it works. 

5. Once you've provided the required details, you will receive your **API ID** and **API Hash**.

6. Open `config` folder and create file `config-tg-yourusername.ini`. Enter API ID, API Hash and phone number.
    - Important: User needs to name the config file as `config-tg-yourusername.ini` (for example, `config-tg-houston.ini`). Username will be used to create `.session` file. Do not change the name of the config file after the first initialization and authorization. Username can be any set of alphabetic characters (letters). There cannot be two clients with the same username. Behaviour of each client will be written in the `applicationMain.log` file.
### Database configuration

1. Visit the [MongoDB download page](https://www.mongodb.com/try/download/community) and download Community Server. 

2. The easiest installation is through Windows installer (.msi), choosing "Run Service as Network Service user".

3. Optionally, change path to the logs and data folders.

4. In the `config` folder update `config-database-script-params.ini` file with the path to the server (port:27017 by default, or change it at `bin/mongo.cfg`) and the names for the database and collections.

5. Optionally change the database name. If changing collection names, keep the same meaning, e.g. keep variable `collection1` so it corresponds to the information regarding the chat, keep `collection2` so it corresponds to the messages.

### Installation

1. Clone the repo.

2. Install `requirements.txt`.

3. Open folder `config` and enter api details in the Telegram config file. Refer to the section "Obtaining Credentials for Telegram API". Example of the config file is in the `config` folder under the name `example_config-tg-houston.ini`. If you would decide to have 'houston' as username, you would have to delete 'example_'. 

4. Open folder `config` and enter database connection details. Refer to the section "Database configuration".  Example of the database config file is in the `config` folder. 

5. Write input chats in the text file, each on a new line.

6. File `config-database-script-params.ini` has options to define `max_run_time` (the time script should run in minutes) and `max_iterations` (the number of iterations before the termination of the script).
    - Important: Script will run more than a specified run time, up until all of the chats from the current iteration have been processed.

6. Run the script.

7. Upon executing the script for the first time or when utilizing a new Telegram account, you will be asked to provide the phone number linked to your account. If you're initializing multiple accounts, the details of the account undergoing authorization will be displayed in the terminal. Simply copy and paste the phone number. Subsequently, an authorization check will be sent to your Telegram account in the form of a message. The terminal will prompt you to enter the received code.

### Restart of the script
The script stores information about processed chats and iteration number in the `temp_var` folder located in the project's root directory. This functionality allows the script to resume from where it left off. Therefore, if the user intends to modify the `input_chats.txt` file and rerun the script with a new set of channels, they should delete the `temp_var` folder. Additionally, to maintain a consistent workflow, the user should update the database name in the `config-database-script-params.ini` file.


<!-- Code explanation -->
## Code Explanation

### General Overview
The user specifies input chats, and the script proceeds to iterate through them. For each input chat, it retrieves and stores messages and it captures the details about the chat. The script treats channels and groups interchangeably without explicit differentiation. If a channel is an input parameter for participants retrieval, the script continues without accessing participants. 

Furthermore, the script generates a list of mentioned chats associated with each input chat. These mentioned chats are sourced from messages that have been forwarded to the chat ( Message object's endpoint: `fwd_from.from_id.channel_id`), the `linked_chat_id` endpoint of the chat info document, and parsing actual messages to identify links to other chats. Once all input chats have been processed, the chats mentioned in those inputs become the new input for the subsequent iteration. This process repeats until the specified time limit or iteration number is reached. 

Aforementioned mentioned chats are saved in a seprate collection.

In the next sections, general flowchart, network, restart logic and multi-client/ratelimit issue are shown.
   
### Flowchart

<div align="center">
  <img src="img/flowchart.png" alt="flowchart">
</div>

### Restart logic
Script can be terminated at any point in time, and it will continue where it stopped. 
Potentially, if it is terminated during message retrieval, and chat info is already written in the database, next initialization will write the same chat information once again. Similarly, if the script is terminted during the retrieval of the participants, next intialization will write messages and chat info in the database once again. This redundancy problem was not addressed in order to keep data retrieval simple and in order to wait for the potential upgrade of the script to update database with the new messages from the processed chats. 

In practice, there is a really small chance to anything, but the chat infromation written more than once.

### Network/Iteration logic

<div align="center">
  <img src="img/networklogic.png" alt="flowchart">
</div>


### Mulit-client and ratelimit logic
Script uses asyncio Queue() object to store chats that are being processed in the current iteration. Script assigns the same task to each of the clients, but Queue object is in charge of assigning one chat to one client, thus we do not have overlap of client-chat processes.

As soon as one client hits rate limits, script puts it to sleep for the amount of time stated in the rate limit error. The while loop is initiated and each 15 minutes, it checks if any of the clients have finished the task. This implies that there are no more chats in the Queue that could be assigned to our sleeping client i.e. iteration is finished. As the next iteration starts, our client will try to access the chat, and if there is still a need to wait, it will sleep until it can work again, and periodically check if the iteration is over.

<!-- DB Data Structure -->
## DB Data Structure
Database consists of 4 collections. Example of a document for each collection is <a href="https://git.sbg.ac.at/geo-social-analytics/geo-social-media/telegram-crawler/-/tree/main/database_samples">here</a> (on gitlab) or [here](./database_samples) (if you cloned the repository to your local machine).

<div align="center">
  <img src="img/db_diagram.png" alt="db_diagram">
</div>

There is also another, fifth collection, used to track validity of the processed chats. Main use is to filter processed chats before each iteration. 

<!-- Queries example and tips -->
## Queries example and tips
Check notebooks with tips and examples on how to query data retrieved from Telegram <a href="https://git.sbg.ac.at/geo-social-analytics/geo-social-media/telegram-crawler/-/tree/main/queries">here</a> (on gitlab) or [here](./queries) (if you cloned the repository to your local machine).


<!-- Problems/questions/doubts -->
## Problems/Questions/Doubts

See the [open issues](https://git.sbg.ac.at/geo-social-analytics/geo-social-media/telegram-crawler/-/issues) for a full list of proposed features (and known issues).

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* []() Nefta
* []() David

<p align="right">(<a href="#readme-top">back to top</a>)</p>
