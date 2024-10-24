import os
import glob
import re
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

# Specify the directory containing the log files
directory_path = "../../logs"

# Use glob to get all files in the directory
file_list = glob.glob(os.path.join(directory_path, "*"))

# Check if there are files in the directory
if file_list:
    # Get the most recently modified file by sorting with the modification time
    # latest_file = max(file_list, key=os.path.getmtime)
    latest_file = "../../logs/2024-09-01T190239.log"
    # Open and read the latest file
    with open(latest_file, "r") as file:
        log_data = file.read()

    print(f"Latest file '{latest_file}' read successfully.")
else:
    print("No files found in the directory.")
    exit(1)

# Initialize dictionaries to hold coordinates, results, and meta info
all_runs_data = []
current_run_data = {"experiment_results": {}, "global_points": {}, "voltage": None, "repeat": None}

# Regular expressions to match coordinates, positions, and values
coord_pattern = re.compile(r"Point2D\((\d+\.\d+), (\d+\.\d+)\)")
global_coord_pattern = re.compile(r"Moving to < X(\d+\.\d+) Y(\d+\.\d+)>")
type_pattern = re.compile(r"'type': '(\w+)'")
position_pattern = re.compile(r"I'm at position (\d+)")
meta_pattern = re.compile(r"'voltage': (\d+), 'repeat': (\d+), 'type': '(\w+)'")

current_point = None
highest_x = lowest_x = highest_y = lowest_y = None


# Function to reset data for a new run
def reset_run_data():
    global highest_x, lowest_x, highest_y, lowest_y
    highest_x = lowest_x = highest_y = lowest_y = None
    return {"experiment_results": {}, "global_points": {}, "voltage": None, "repeat": None}


# Parse log data to extract coordinates and types
for line in log_data.split("\n"):
    # Find global movement coordinates
    global_coord_match = global_coord_pattern.search(line)
    if global_coord_match and current_point is not None:
        global_x, global_y = float(global_coord_match.group(1)), float(global_coord_match.group(2))
        current_run_data["global_points"][current_point] = (global_x, global_y)

    # Find local Point2D coordinates
    coord_match = coord_pattern.search(line)
    if coord_match:
        x, y = float(coord_match.group(1)), float(coord_match.group(2))
        current_point = (x, y)
        if current_point not in current_run_data["experiment_results"]:
            current_run_data["experiment_results"][current_point] = []

        # Track highest/lowest x and y values
        if highest_x is None or x > highest_x[0]:
            highest_x = (x, y)
        if lowest_x is None or x < lowest_x[0]:
            lowest_x = (x, y)
        if highest_y is None or y > highest_y[1]:
            highest_y = (x, y)
        if lowest_y is None or y < lowest_y[1]:
            lowest_y = (x, y)

    # Find type and meta values
    type_match = type_pattern.search(line)
    meta_match = meta_pattern.search(line)
    if type_match and current_point is not None:
        result_type = type_match.group(1)
        if current_point in current_run_data["experiment_results"]:
            current_run_data["experiment_results"][current_point].append(result_type)

    if meta_match:
        current_run_data["voltage"] = meta_match.group(1)
        current_run_data["repeat"] = meta_match.group(2)

    # Check for position reset to detect a new run
    position_match = position_pattern.search(line)
    if position_match:
        position = int(position_match.group(1))
        if position == 1 and len(current_run_data["experiment_results"]) > 0:
            all_runs_data.append(current_run_data)
            current_run_data = reset_run_data()

# Append the last run if it exists
if len(current_run_data["experiment_results"]) > 0:
    all_runs_data.append(current_run_data)

# Define colors for each type
color_map = {
    "no_effect": "blue",
    "reboot": "green",
    "no_response": "red",
    "glitch": "purple",
    "error": "orange",
}


# Function to draw pie chart markers
def draw_pie(ax, x, y, colors, size=100):
    start_angle = 0
    for color in colors:
        wedge = Wedge(
            (x, y), size, start_angle, start_angle + 180, color=color, transform=ax.transData._b
        )
        ax.add_patch(wedge)
        start_angle += 180


# Plotting the runs
for run_index, run_data in enumerate(all_runs_data):
    experiment_results = run_data["experiment_results"]
    global_points = run_data["global_points"]
    voltage = run_data["voltage"]
    repeat = run_data["repeat"]

    # Set up the plot
    plt.figure(figsize=(10, 6))
    ax = plt.gca()

    # Plot each point with multiple colors
    for point, types in experiment_results.items():
        unique_types = set(types)
        colors = [color_map[t] for t in unique_types]
        draw_pie(
            ax, point[0], point[1], colors, size=0.02
        )  # size is adjusted for scatter plot scaling

    # Plot global points for highest/lowest values
    if highest_x:
        global_highest_x = global_points.get(highest_x, None)
        if global_highest_x:
            plt.text(
                highest_x[0],
                highest_x[1],
                f"({global_highest_x[0]:.2f}, {global_highest_x[1]:.2f})",
                fontsize=8,
                ha="right",
            )

    if lowest_x:
        global_lowest_x = global_points.get(lowest_x, None)
        if global_lowest_x:
            plt.text(
                lowest_x[0],
                lowest_x[1],
                f"({global_lowest_x[0]:.2f}, {global_lowest_x[1]:.2f})",
                fontsize=8,
                ha="left",
            )

    if highest_y:
        global_highest_y = global_points.get(highest_y, None)
        if global_highest_y:
            plt.text(
                highest_y[0],
                highest_y[1],
                f"({global_highest_y[0]:.2f}, {global_highest_y[1]:.2f})",
                fontsize=8,
                va="bottom",
            )

    if lowest_y:
        global_lowest_y = global_points.get(lowest_y, None)
        if global_lowest_y:
            plt.text(
                lowest_y[0],
                lowest_y[1],
                f"({global_lowest_y[0]:.2f}, {global_lowest_y[1]:.2f})",
                fontsize=8,
                va="top",
            )

    # Label the plot
    plt.title(f"EMFI Research Test Results - Run {run_index + 1}")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True)
    plt.legend([f"Voltage: {voltage}, Repeat: {repeat}"], loc="upper right")
    plt.show()
