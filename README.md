# Telegram Crawler

This script allows you to crawl through Telegram chats and retrieve mentioned chats in a hierarchical manner. It supports multiple levels of crawling based on the number of iterations specified.

## Prerequisites

Before running the script, make sure you have the following:

- Python 3.x installed on your machine
- Required Python packages installed (can be installed via `pip install`):
  - telethon==1.25.2

## Getting Started

1. Clone the repository or download the script files to your local machine.

2. Install the required packages by running the following command in your terminal or command prompt:

   ```bash
   pip install telethon

3. Open the `config-bastiaugen.ini` file and update the configuration values according to your needs:

- Replace `<your_api_id>` and `<your_api_hash>` with your Telegram API development credentials. You can obtain these credentials from the Telegram API Development Tools.

- Replace `<your_phone_number>` with your full phone number, including the country code and the `+` symbol.

- Replace `<your_username>` with your Telegram username.

- Set `<number_of_levels>` to the desired depth/iterations for crawling.

4. Create a text file named `input_chats.txt` and add the chats you want to crawl, each on a new line.

5. Run the script. The script will start crawling through the channels and retrieve mentioned channels.

6. The crawled data will be saved to a JSON file named `YYYYMMDD_HHMMSS_level_data.json`, where `YYYYMMDD_HHMMSS` represents the current timestamp.

## Notes

- The script uses the Telethon library to interact with the Telegram API.
- Channels mentioned within the messages of the crawled channels will be retrieved in a hierarchical manner based on the specified number of levels.
- The crawled data will be stored in a JSON file with the following structure:

```json
{
"level0": {
 "channel_1": ["mentioned_channel_1", "mentioned_channel_2"],
 "channel_2": ["mentioned_channel_3"]
},
"level1": {
 "mentioned_channel_1": ["mentioned_channel_4"],
 "mentioned_channel_2": [],
 "mentioned_channel_3": []
},
"level2": {
 "mentioned_channel_4": []
}
}
