import os
import glob
import re
import matplotlib.pyplot as plt
import numpy as np

# Specify the directory containing the log files
directory_path = "../../logs"

# Use glob to get all files in the directory
file_list = glob.glob(os.path.join(directory_path, "*"))

# Check if there are files in the directory
if file_list:
    latest_file = max(file_list, key=os.path.getmtime)
    # latest_file = '../../logs/2024-09-14T200928.log'
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
global_highest_x = global_highest_y = global_lowest_x = global_lowest_y = None
first_run = True


# Function to reset data for a new run
def reset_run_data():
    global highest_x, lowest_x, highest_y, lowest_y
    highest_x = lowest_x = highest_y = lowest_y = None
    return {"experiment_results": {}, "global_points": {}, "voltage": None, "repeat": None}


# Parse log data to extract coordinates and types
for line in log_data.split("\n"):
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

    coord_match = coord_pattern.search(line)
    if coord_match:
        x, y = float(coord_match.group(1)), float(coord_match.group(2))
        current_point = (x, y)
        if current_point not in current_run_data["experiment_results"]:
            current_run_data["experiment_results"][current_point] = []

    type_match = type_pattern.search(line)
    meta_match = meta_pattern.search(line)
    if type_match and current_point is not None:
        result_type = type_match.group(1)
        if current_point in current_run_data["experiment_results"]:
            current_run_data["experiment_results"][current_point].append(result_type)

    if meta_match:
        current_run_data["voltage"] = meta_match.group(1)
        current_run_data["repeat"] = meta_match.group(2)

    position_match = position_pattern.search(line)
    if position_match:
        position = int(position_match.group(1))
        if position == 1 and len(current_run_data["experiment_results"]) > 0:
            if not first_run:
                all_runs_data.append(current_run_data)
            first_run = False
            current_run_data = reset_run_data()
            current_run_data["experiment_results"][current_point] = []

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


# Function to determine the color of a point
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


# Batch size for runs
batch_size = 20
total_batches = int(np.ceil(len(all_runs_data) / batch_size))

# Specify the list of run numbers to exclude (1-based index)
excluded_runs = []  # Example: exclude runs 3, 5, and 7

newpath = f"../../plots/{latest_file[-21:-4]}"
if not os.path.exists(newpath):
    os.makedirs(newpath)
    print(f"created new directory {newpath}")

# Plot each batch of runs
run_counter = 1  # Initialize the global run counter
for batch_num in range(total_batches):
    start_idx = batch_num * batch_size
    end_idx = min((batch_num + 1) * batch_size, len(all_runs_data))

    # Collect the runs to plot, excluding the specified runs
    runs_to_plot = [
        (i + start_idx, run)
        for i, run in enumerate(all_runs_data[start_idx:end_idx])
        if (i + 1 + start_idx) not in excluded_runs
    ]

    if not runs_to_plot:
        print(f"No runs to plot in batch {batch_num + 1} due to exclusions.")
        continue

    # Create a figure for the current batch of runs
    num_runs = len(runs_to_plot)
    fig, axes = plt.subplots(
        nrows=int(np.ceil(num_runs / 2)), ncols=2, figsize=(16, 8 * int(np.ceil(num_runs / 2)))
    )

    if num_runs > 1:
        axes = axes.flatten()
    else:
        axes = [axes]

    # Plot each run in the batch
    for (index, run_data), ax in zip(runs_to_plot, axes):
        global_points = run_data["global_points"]
        experiment_results = run_data["experiment_results"]
        voltage = run_data["voltage"]
        repeat = run_data["repeat"]

        # Info message for debugging
        print(f"Plotting Run {run_counter}, Number of Points: {len(global_points)}")

        for point, global_point in global_points.items():
            if point in experiment_results:
                color = determine_color(experiment_results[point])
                ax.scatter(global_point[0], global_point[1], color=color, s=20)

        meta_data = f"Voltage: {voltage}, Repeat: {repeat}"
        ax.annotate(
            meta_data,
            xy=(0.5, 1.1),
            xycoords="axes fraction",
            fontsize=10,
            ha="center",
            va="bottom",
            bbox=dict(facecolor="white", alpha=0.5),
        )

        ax.set_title(f"Run {run_counter}")
        ax.set_xlabel("X Coordinate")
        ax.set_ylabel("Y Coordinate")
        ax.set_xlim(global_lowest_x, global_highest_x)
        ax.set_ylim(global_lowest_y, global_highest_y)
        ax.grid(True)

        # Increment the global run counter
        run_counter += 1

    fig.legend(
        handles=[
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
                markerfacecolor=color_map["error"],
                markersize=12,
                label="Error",
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
        ],
        loc="upper center",
        borderaxespad=0.0,
        fontsize=12,
        title="Global Coordinates",
    )

    fig.subplots_adjust(top=0.88)
    plt.tight_layout(rect=[0, 0, 1, 0.98])

    # Save the plot
    plot_path = os.path.join(newpath, f"batch_{batch_num + 1}.png")
    plt.show()
    plt.close()

print("Plotting complete.")
