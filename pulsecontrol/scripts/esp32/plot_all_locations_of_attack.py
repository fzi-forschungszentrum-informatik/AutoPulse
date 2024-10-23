import os
import glob
import re
import matplotlib.pyplot as plt

from scripts.esp32.plot_search_area_relative import plot_chip_with_experiment_rect

# Specify the directory containing the log files
directory_path = "../../logs"

MARGIN_PERCENTAGE = 0.03
MIN_EXPERIMENTS = 300
MAX_NUMBER_OF_PLOTS = 10
PLOT_ALL_AFTER_SPECIFIED = False
SHOW_RESULTS = True
SHOW_AREA = True


def extract_meta_data(log_file):
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


def plot_single(log_file_path):
    if os.path.isfile(log_file_path):
        with open(log_file_path, "r") as file:
            log_data = file.read()
    else:
        print("Invalid file path: {p}".format(p=log_file_path))
        exit(1)

    # Initialize dictionaries to hold coordinates, results, and meta info
    all_runs_data = []
    current_run_data = {"experiment_results": {}, "global_points": {}}
    experiment_count = 0

    # Regular expressions to match coordinates, positions, and values
    coord_pattern = re.compile(r"Point2D\((\d+\.\d+), (\d+\.\d+)\)")
    global_coord_pattern = re.compile(r"Moving to < X(\d+\.\d+) Y(\d+\.\d+)>")
    type_pattern = re.compile(r"'type': '(\w+)'")
    type_pattern_old = re.compile(r"'type': <EMPEffect\..*?: '(\w+)'")
    success_pattern = re.compile(r"Success: {'success':")  # To identify experiments

    meta_data = extract_meta_data(log_file_path)
    variance = offset_range = voltage_range = repeat_range = None
    if meta_data:
        if meta_data.get("movement_strategy"):
            variance = meta_data["movement_strategy"]["var"]
        if meta_data.get("offset"):
            start = meta_data["offset"]["start"]
            end = meta_data["offset"]["end"]
            if start == end:
                offset_range = f"{meta_data['offset']['start']}"
            else:
                offset_range = f"{meta_data['offset']['start']}-{meta_data['offset']['end']}"
        if meta_data.get("voltage"):
            lower = meta_data["voltage"]["lower"]
            upper = meta_data["voltage"]["upper"]
            if lower == upper:
                voltage_range = f"{meta_data['voltage']['lower']}"
            else:
                voltage_range = f"{meta_data['voltage']['lower']}-{meta_data['voltage']['upper']}"
        if meta_data.get("repeat"):
            lower = meta_data["repeat"]["lower"]
            upper = meta_data["repeat"]["upper"]
            if lower == upper:
                repeat_range = f"{meta_data['repeat']['lower']}"
            else:
                repeat_range = f"{meta_data['repeat']['lower']}-{meta_data['repeat']['upper']}"

    current_point = None
    global_highest_x = global_highest_y = global_lowest_x = global_lowest_y = None

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

        # Find type and add to current point (if it's part of an experiment line)
        type_match = type_pattern.search(line)
        if type_match and current_point is not None:
            experiment_count += 1
            result_type = type_match.group(1)
            if current_point in current_run_data["experiment_results"]:
                current_run_data["experiment_results"][current_point].append(result_type)
        else:
            old_type_match = type_pattern_old.search(line)
            if old_type_match and current_point is not None:
                experiment_count += 1
                result_type = old_type_match.group(1)
                if current_point in current_run_data["experiment_results"]:
                    current_run_data["experiment_results"][current_point].append(result_type)

    # Append the last run if it exists
    if len(current_run_data["experiment_results"]) > 0:
        all_runs_data.append(current_run_data)

    if experiment_count <= 1:
        print(f"No experiments found for run {log_file_path}")
        return

    if experiment_count <= MIN_EXPERIMENTS:
        print(
            f"Skipping {log_file_path}, only {experiment_count} experiments found. Decrease MIN_EXPERIMENTS."
        )
        return

    # Define colors for each type

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
    if SHOW_RESULTS:
        # Create a single plot
        fig, ax = plt.subplots(figsize=(10, 8))

        # Plot each point with the highest priority color
        for point, global_point in global_points.items():
            if point in final_results:
                color = determine_color(final_results[point])
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
        ax.set_title(f"EMFI Attack - {log_file_path[-21:-4]}")
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
            f"Max Y: {global_highest_y}, Min Y: {global_lowest_y}\n"
            f"Var: {variance}, Voltage: {voltage_range}, Repeat: {repeat_range}, "
            f"Offset: {offset_range}, Experiments: {experiment_count}"
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
        print(f"plotting {log_file_path}")
        plt.show()
    if SHOW_AREA:
        print(f"plotting relative attack location")
        plot_chip_with_experiment_rect(
            116.890135215,
            122.836141265,
            120.29093649,
            126.18395469,
            global_lowest_x,
            global_highest_x,
            global_lowest_y,
            global_highest_y,
            log_file_path,
        )


log_files = [
    # '../../logs/2024-09-01T190239.log',
    # '../../logs/2024-09-01T234300.log',
    # '../../logs/2024-09-02T190332.log',
    # '../../logs/2024-09-02T190332.log',
    # '../../logs/2024-09-03T170925.log'
    # '../../logs/2024-09-03T210708.log'
    # '../../logs/2024-09-04T192301.log',
    # '../../logs/2024-09-05T110313.log',
    # '../../logs/2024-09-06T154733.log'
    # '../../logs/2024-09-08T131657.log',
    # '../../logs/2024-09-14T200928.log'
]
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
elif PLOT_ALL_AFTER_SPECIFIED:
    # Find the creation/modification time of the specified log file
    specified_file = log_files[0]
    specified_time = os.path.getmtime(specified_file)
    # Get all files in the directory
    all_log_files = glob.glob(os.path.join(directory_path, "*"))
    # Filter files that were created/modified after the specified file
    log_files = [
        log_file for log_file in all_log_files if os.path.getmtime(log_file) > specified_time
    ]
    if not log_files:
        print(f"No log files found after {specified_file}.")
        exit(1)
    else:
        print(f"Found {len(log_files)} log files created after {specified_file}.")

batch_size = 0
for log_file in log_files:
    if batch_size == 10:
        input("Press Enter to continue plotting...")
        print("Continuing script execution...")
        batch_size = 0
    batch_size += 1
    plot_single(log_file)
