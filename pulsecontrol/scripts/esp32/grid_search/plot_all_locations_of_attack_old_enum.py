import os
import glob
import re
import matplotlib.pyplot as plt

# Specify the directory containing the log files
directory_path = "../../../logs"
print("current directory: {pwd}".format(pwd=os.getcwd()))

# Use glob to get all files in the directory
file_list = glob.glob(os.path.join(directory_path, "*"))

# Check if there are files in the directory
if file_list:
    # Get the most recently modified file by sorting with the modification time
    # latest_file = max(file_list, key=os.path.getmtime)
    latest_file = "../../../logs/2024-09-01T190239.log"
    # Open and read the latest file
    with open(latest_file, "r") as file:
        log_data = file.read()

    print(f"Latest file '{latest_file}' read successfully.")
else:
    print("No files found in the directory.")
    exit(1)

# Initialize dictionaries to hold coordinates, results, and meta info
all_runs_data = []
current_run_data = {"experiment_results": {}, "global_points": {}}

# Regular expressions to match coordinates, positions, and values
coord_pattern = re.compile(r"Point2D\((\d+\.\d+), (\d+\.\d+)\)")
global_coord_pattern = re.compile(r"Moving to < X(\d+\.\d+) Y(\d+\.\d+)>")
type_pattern = re.compile(r"'type': <EMPEffect.ERROR: '(\w+)'")
success_pattern = re.compile(r"Success: {'success':")  # To identify experiments

current_point = None
global_highest_x = global_highest_y = global_lowest_x = global_lowest_y = None

# Parse log data to extract coordinates and types
for line in log_data.split("\n"):
    # Find global movement coordinates
    global_coord_match = global_coord_pattern.search(line)
    if global_coord_match and current_point is not None:
        global_x, global_y = float(global_coord_match.group(1)), float(global_coord_match.group(2))
        current_run_data["global_points"][current_point] = (global_x, global_y)
        if global_highest_x is None or global_x > global_highest_x:
            global_highest_x = global_x
        if global_lowest_x is None or global_x < global_lowest_x:
            global_lowest_x = global_x
        if global_highest_y is None or global_y > global_highest_y:
            global_highest_y = global_y
        if global_lowest_y is None or global_y < global_lowest_y:
            global_lowest_y = global_y

    # Find local Point2D coordinates
    coord_match = coord_pattern.search(line)
    if coord_match:
        x, y = float(coord_match.group(1)), float(coord_match.group(2))
        current_point = (x, y)
        if current_point not in current_run_data["experiment_results"]:
            current_run_data["experiment_results"][current_point] = []

    # Find type and add to current point (if it's part of an experiment line)
    type_match = type_pattern.search(line)
    if type_match and current_point is not None:
        result_type = type_match.group(1)
        if current_point in current_run_data["experiment_results"]:
            current_run_data["experiment_results"][current_point].append(result_type)

# Append the last run if it exists
if len(current_run_data["experiment_results"]) > 0:
    all_runs_data.append(current_run_data)

# Define colors for each type
color_map = {
    "no_effect": "blue",
    "reboot": "green",
    "no_response": "purple",
    "glitch": "red",
    "error": "orange",
}


# Function to determine the color of a point based on priority
def determine_color(types):
    unique_types = set(types)
    if "glitch" in unique_types:
        return color_map["glitch"]
    elif "error" in unique_types:
        return color_map["error"]
    elif "reboot" in unique_types:
        return color_map["reboot"]
    elif "no_response" in unique_types:
        return color_map["no_response"]
    else:
        return color_map["no_effect"]


# Dictionary to store the final results with the highest priority for each point
final_results = {}

# Group all runs and determine the highest priority color for each point
for run_data in all_runs_data:
    global_points = run_data["global_points"]
    experiment_results = run_data["experiment_results"]

    for point, global_point in global_points.items():
        if point in experiment_results:
            # Combine experiment results for this point
            if point not in final_results:
                final_results[point] = experiment_results[point]
            else:
                final_results[point].extend(experiment_results[point])

# Create a single plot
fig, ax = plt.subplots(figsize=(10, 8))

# Plot each point with the highest priority color
for point, global_point in global_points.items():
    if point in final_results:
        color = determine_color(final_results[point])
        ax.scatter(global_point[0], global_point[1], color=color, s=20)

# Set axis labels and title
ax.set_title(f"All Runs Combined with Grid Search - {latest_file[-21:-4]}")
ax.set_xlabel("X Coordinate")
ax.set_ylabel("Y Coordinate")

# Set consistent axis limits for the combined plot
ax.set_xlim(global_lowest_x, global_highest_x)
ax.set_ylim(global_lowest_y, global_highest_y)
ax.grid(True)

# Create a color legend
color_legend = [
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=color_map["glitch"],
        markersize=12,
        label="Glitch",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=color_map["error"],
        markersize=12,
        label="Error",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=color_map["reboot"],
        markersize=12,
        label="Reboot",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=color_map["no_response"],
        markersize=12,
        label="No Response",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=color_map["no_effect"],
        markersize=12,
        label="No Effect",
    ),
]

# Add the global highest and lowest x/y values in a second line below the legend
global_info_text = (
    f"Max X: {global_highest_x}, Min X: {global_lowest_x}, "
    f"Max Y: {global_highest_y}, Min Y: {global_lowest_y}"
)

# Place the legend below the plot in one line
fig.legend(
    handles=color_legend,
    loc="lower center",
    ncol=5,
    title=global_info_text,
    title_fontsize="x-large",
    fontsize=12,
)

# Adjust layout and show the plot
plt.tight_layout(rect=(0, 0.1, 1, 1))
print("plotting all points in a single coordination system with highest priority colors...")
plt.show()
