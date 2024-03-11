import numpy as np
import pytest
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
from more_itertools import take
from pytest import approx

from pulsecontrol.helpers import Point2D
from pulsecontrol.strategies.movement.fix_point import FixPoint
from pulsecontrol.strategies.movement.gaussian import Gaussian
from pulsecontrol.strategies.movement.grid import Grid


def test_grid():
    grid = Grid(step_x=3, step_y=4)
    expected = [
        (1 / 3, 1 / 4),
        (2 / 3, 1 / 4),
        (1 / 3, 2 / 4),
        (2 / 3, 2 / 4),
        (1 / 3, 3 / 4),
        (2 / 3, 3 / 4),
    ]
    assert expected == list(grid)


@pytest.mark.skip("Only needed to generate the plot image")
def test_sample_gaussian():
    gaussian = Gaussian(var=3, center=Point2D(0, 0))
    data = np.array(take(3000, gaussian))
    fig, ax = plt.subplots(tight_layout=True)
    ax.hist2d(data[:, 0], data[:, 1], bins=40)
    plt.show()


def test_display_grid():
    grid = Grid(step_x=3, step_y=4)
    data = np.array(list(grid))
    plt.scatter(data[:, 0], data[:, 1], marker="x", color="blue", label="Injection Location")

    # Create the rectangle patch and add it to the plot
    rectangle = Rectangle((0, 0), 1, 1, linewidth=2, edgecolor="red", fill=False)
    plt.gca().add_patch(rectangle)

    # Add a label to the rectangle
    rect_label = "Chip Outline"
    location = 0.04
    plt.text(location, location, rect_label, fontsize=10, color="red")

    # Axis settings
    plt.xlim(-0.1, 1.1)
    plt.ylim(-0.1, 1.1)
    # plt.xlabel('X-axis')
    # plt.ylabel('Y-axis')
    plt.legend()
    plt.show()


def test_fix_point_movement():
    fix_point = FixPoint(position=Point2D(0.321, 0.5543))
    for x, y in take(20, fix_point):
        assert 0.321 == approx(x)
        assert 0.5543 == approx(y)
