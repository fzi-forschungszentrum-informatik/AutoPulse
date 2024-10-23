import json
import re


# Function to extract the first valid JSON block from the log
def extract_json_from_log(log_data):
    # Adjust the regular expression to match the first valid JSON block
    json_pattern = re.compile(r'\{.*?"movement_strategy".*?\}', re.DOTALL)
    json_match = json_pattern.search(log_data)
    print("extracting")

    if json_match:
        json_str = json_match.group(0)  # Extract the matched JSON string
        try:
            json_data = json.loads(json_str)  # Try to parse the JSON
            return json_data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None
    return None


# Function to read and process the log
def process_log_file(log_file):
    with open(log_file, "r") as file:
        log_data = file.read()

    # Extract and parse the JSON block
    json_data = extract_json_from_log(log_data)
    if json_data:
        print("JSON data successfully extracted and parsed:")
        # print(json.dumps(json_data, indent=4))
    else:
        print("No valid JSON data found.")


process_log_file("../../logs/2024-09-12T102753.log")
