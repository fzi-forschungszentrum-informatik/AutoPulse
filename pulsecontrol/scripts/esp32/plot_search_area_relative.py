import matplotlib.pyplot as plt
import matplotlib.patches as patches


# Function to plot the chip rectangle and the smaller experiment rectangle inside it
def plot_chip_with_experiment_rect(
    chip_min_x,
    chip_max_x,
    chip_min_y,
    chip_max_y,
    exp_min_x,
    exp_max_x,
    exp_min_y,
    exp_max_y,
    log_file,
):
    # Determine the coordinate system boundaries
    overall_min_x = min(chip_min_x, exp_min_x)
    overall_max_x = max(chip_max_x, exp_max_x)
    overall_min_y = min(chip_min_y, exp_min_y)
    overall_max_y = max(chip_max_y, exp_max_y)

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot the chip rectangle (larger outer rectangle)
    chip_width = chip_max_x - chip_min_x
    chip_height = chip_max_y - chip_min_y
    chip_rect = patches.Rectangle(
        (chip_min_x, chip_min_y),
        chip_width,
        chip_height,
        linewidth=2,
        edgecolor="blue",
        facecolor="none",
        label="Chip Boundary",
    )

    # Add the chip rectangle to the plot
    ax.add_patch(chip_rect)

    # Plot the experiment rectangle (smaller inner rectangle in red)
    exp_width = exp_max_x - exp_min_x
    exp_height = exp_max_y - exp_min_y
    exp_rect = patches.Rectangle(
        (exp_min_x, exp_min_y),
        exp_width,
        exp_height,
        linewidth=2,
        edgecolor="red",
        facecolor="none",
        label="Attack Area",
    )

    # Add the experiment rectangle to the plot
    ax.add_patch(exp_rect)

    # Set axis labels and title
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.set_title(f"Chip Boundary with Attack Area - {log_file[-21:-4]}")

    # Set axis limits based on the combined chip and experiment dimensions
    ax.set_xlim(overall_min_x, overall_max_x)
    ax.set_ylim(overall_min_y, overall_max_y)

    # Add a grid and legend
    ax.grid(True)
    ax.legend(loc="upper right")

    # Display the plot
    plt.tight_layout()
    plt.show()
