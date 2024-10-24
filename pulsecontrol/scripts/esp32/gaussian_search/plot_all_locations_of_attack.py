import os
import glob
import re
import json
import matplotlib.pyplot as plt


# Specify the directory containing the log files
directory_path = "../../../logs"

# User-specified list of files to process
log_files = [
    "../../../logs/2024-09-10T115711.log"
    # Add more files here as needed
]


# Function to extract specific values from the log
def extract_values_from_log(log_file):
    with open(log_file, "r") as file:
        log_data = file.read()

    # Define regex patterns for each part of the log you're interested in
    movement_strategy_pattern = re.compile(
        r'"movement_strategy":\s*\{\s*"var":\s*([\d\.]+),\s*"center":\s*\[\s*([\d\.]+),\s*([\d\.]+)\s*\],\s*"iterations":\s*(\d+)\s*\}'
    )
    offset_pattern = re.compile(
        r'"offset":\s*\{\s*"start":\s*(\d+),\s*"end":\s*(\d+),\s*"step":\s*(\d+)\s*\}'
    )
    voltage_pattern = re.compile(r'"voltage":\s*\{\s*"lower":\s*(\d+),\s*"upper":\s*(\d+)\s*\}')
    repeat_pattern = re.compile(r'"repeat":\s*\{\s*"lower":\s*(\d+),\s*"upper":\s*(\d+)\s*\}')

    # Search the log for each pattern
    movement_strategy_match = movement_strategy_pattern.search(log_data)
    offset_match = offset_pattern.search(log_data)
    voltage_match = voltage_pattern.search(log_data)
    repeat_match = repeat_pattern.search(log_data)

    # Extract and store the values if matches are found
    extracted_values = {}

    if movement_strategy_match:
        extracted_values["movement_strategy"] = {
            "var": float(movement_strategy_match.group(1)),
            "center": [
                float(movement_strategy_match.group(2)),
                float(movement_strategy_match.group(3)),
            ],
            "iterations": int(movement_strategy_match.group(4)),
        }
    if offset_match:
        extracted_values["offset"] = {
            "start": int(offset_match.group(1)),
            "end": int(offset_match.group(2)),
            "step": int(offset_match.group(3)),
        }
    if voltage_match:
        extracted_values["voltage"] = {
            "lower": int(voltage_match.group(1)),
            "upper": int(voltage_match.group(2)),
        }
    if repeat_match:
        extracted_values["repeat"] = {
            "lower": int(repeat_match.group(1)),
            "upper": int(repeat_match.group(2)),
        }

    return extracted_values


if not log_files:
    file_list = glob.glob(os.path.join(directory_path, "*"))

    # Check if there are files in the directory
    if file_list:
        # Get the most recently modified file by sorting with the modification time
        latest_file = max(file_list, key=os.path.getmtime)
        log_files = [latest_file]
        print(f"No log specified, using latest file {latest_file}")

    else:
        print("No files found in the directory.")
        exit(1)

MARGIN_PERCENTAGE = 0.03


# Function to generate the plot for a single log file
def generate_plot_from_log(current_log, exp_count=0):
    print(f"Processing file: {current_log}")

    # Initialize dictionaries to hold coordinates, results, and meta info
    current_run_data = {"experiment_results": {}, "global_points": {}}

    # Regular expressions to match coordinates, positions, and values
    coord_pattern = re.compile(r"Point2D\((\d+\.\d+), (\d+\.\d+)\)")
    global_coord_pattern = re.compile(r"Moving to < X(\d+\.\d+) Y(\d+\.\d+)>")
    type_pattern = re.compile(r"'type': '(\w+)'")

    meta_data = extract_values_from_log(current_log)
    variance = offset_range = voltage_range = repeat_range = None
    if meta_data:
        if meta_data["movement_strategy"]:
            variance = meta_data["movement_strategy"]["var"]
        if meta_data["offset"]:
            offset_range = meta_data["offset"]["end"] - meta_data["offset"]["start"]
        if meta_data["voltage"]:
            voltage_range = meta_data["voltage"]["upper"] - meta_data["voltage"]["lower"]
        if meta_data["repeat"]:
            repeat_range = meta_data["repeat"]["upper"] - meta_data["repeat"]["lower"]

    current_point = None
    global_highest_x = global_highest_y = global_lowest_x = global_lowest_y = None

    # Open and read the log file
    with open(current_log, "r") as file:
        log_data = file.read()

    # Parse log data to extract coordinates and types
    for line in log_data.split("\n"):
        # Find global movement coordinates
        global_coord_match = global_coord_pattern.search(line)
        if global_coord_match and current_point is not None:
            global_x, global_y = (
                float(global_coord_match.group(1)),
                float(global_coord_match.group(2)),
            )
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

        # Find type and add to current point
        type_match = type_pattern.search(line)
        if type_match and current_point is not None:
            exp_count += 1
            result_type = type_match.group(1)
            if current_point in current_run_data["experiment_results"]:
                current_run_data["experiment_results"][current_point].append(result_type)

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

    # Create a single plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot each point from the current run
    global_points = current_run_data["global_points"]
    experiment_results = current_run_data["experiment_results"]

    for point, global_point in global_points.items():
        if point in experiment_results:
            color = determine_color(experiment_results[point])
            ax.scatter(global_point[0], global_point[1], color=color, s=20)

    # Calculate the margin based on the MARGIN_PERCENTAGE and apply it to the axis limits
    x_range = global_highest_x - global_lowest_x
    y_range = global_highest_y - global_lowest_y

    x_margin = MARGIN_PERCENTAGE * x_range
    y_margin = MARGIN_PERCENTAGE * y_range

    # Set axis limits with margin applied
    ax.set_xlim(global_lowest_x - x_margin, global_highest_x + x_margin)
    ax.set_ylim(global_lowest_y - y_margin, global_highest_y + y_margin)

    # Set axis labels and title
    ax.set_title(f"All Runs Combined with Gaussian Search - {current_log[-21:-4]}")
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")

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
        f"Max Y: {global_highest_y}, Min Y: {global_lowest_y}, Experiments: {exp_count}"
    )

    # Place the legend below the plot in one line
    fig.legend(
        handles=color_legend,
        loc="lower center",
        ncol=5,
        title=global_info_text,
        title_fontsize="large",
        fontsize=12,
    )

    # Adjust layout and show the plot
    plt.tight_layout(rect=(0, 0.1, 1, 1))
    plt.show()


# Loop through each file in the user-supplied list and generate the plot
for log_file in log_files:
    if os.path.exists(log_file):
        # process_log_file(log_file)
        generate_plot_from_log(log_file)
    else:
        print(f"File {log_file} does not exist.")
