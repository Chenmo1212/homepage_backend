import json
import requests

# Read JSON data file
with open('backup.json', 'r') as file:
    json_data = json.load(file)

# Extract data list
data_list = json_data.get('data', [])

# Loop through the list of data and send a POST request for bulk import
for data in data_list:
    response = requests.post('http://10.0.4.8:5000/messages', json=data)
    if response.status_code == 200:
        print(f"Data with ID {data['id']} imported successfully.")
    else:
        print(f"Failed to import data with ID {data['id']}. Error: {response.json().get('msg')}")

    # response = requests.delete(f"http://10.0.4.8:5000/admin/messages/{data['id']}")
    # if response.status_code == 200:
    #     print(f"Data with ID {data['id']} deleted successfully.")
    # else:
    #     print(f"Failed to delete data with ID {data['id']}. Error: {response.json().get('msg')}")
