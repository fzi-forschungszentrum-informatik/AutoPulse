import os
import glob
import re
from datetime import datetime

# Specify the directory containing the log files and the target date
directory_path = "../../logs"
target_date_str = "2024-09-01"  # Change this to the desired date
target_date = datetime.strptime(target_date_str, "%Y-%m-%d")


# Function to get the modification date of a file
def get_file_modification_date(file_path):
    return datetime.fromtimestamp(os.path.getmtime(file_path))


# Use glob to get all files in the directory
file_list = glob.glob(os.path.join(directory_path, "*"))

# Regular expression to match "Success" lines in the logs
success_pattern = re.compile(r"Success: {'success':")

# Initialize counter
experiment_count = 0

# Process each log file in the directory
for log_file in file_list:
    # Get the modification date of the file
    file_modification_date = get_file_modification_date(log_file)

    # Only process files modified after the specified date
    if file_modification_date >= target_date:
        with open(log_file, "r") as file:
            log_data = file.read()

        # Count occurrences of the "Success" pattern
        experiment_count += len(success_pattern.findall(log_data))

print(f"Total number of experiments after {target_date_str}: {experiment_count}")
