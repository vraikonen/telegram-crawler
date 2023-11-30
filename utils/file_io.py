import json
import pickle

from datetime import date, datetime


# Functions to parse json date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)


# Saving data into json
def save_level_data(level_data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_level_data.json"

    with open(filename, "w") as outfile:
        json.dump(level_data, outfile, cls=DateTimeEncoder)


# Reading input channels
def read_channels_from_file(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file]
    

# Write pickle 
def write_pickle(data, file_path):
    with open(file_path, 'wb') as file:
        pickle.dump(data, file)

# Read pickle
def read_pickle(file_path):
    with open(file_path, 'rb') as file:
        data = pickle.load(file)
    return data

