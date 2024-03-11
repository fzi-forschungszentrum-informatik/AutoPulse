import os

import cv2
import numpy as np


def convert_images():
    for name in filter(lambda n: n.endswith(".npy"), os.listdir("test/data")):
        if not os.path.isfile(f"test/data/{name[:-4]}.png"):
            image = np.load(f"test/data/{name}")
            _, buffer = cv2.imencode(".png", image)
            with open(f"test/data/{name[:-4]}.png", "wb") as outfile:
                outfile.write(buffer.tobytes())


if __name__ == "__main__":
    convert_images()
