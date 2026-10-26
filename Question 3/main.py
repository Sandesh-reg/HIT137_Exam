import cv2
import numpy as np
import math
import os


# Apply the scrambling transformations to a tile
def transform_tile(tile, index, row, col):
    if index % 4 == 0:
        tile = cv2.rotate(tile, cv2.ROTATE_90_CLOCKWISE)
    elif index % 4 == 1:
        tile = cv2.flip(tile, 1)
    elif index % 4 == 2:
        tile = cv2.rotate(tile, cv2.ROTATE_180)
    else:
        tile = cv2.flip(tile, 0)

    if index % 3 == 0:
        tile = 255 - tile

    if row == col:
        tile = tile[:, :, [2, 1, 0]]

    return tile.copy()


# Undo the transformations in reverse order
def restore_tile(tile, index, row, col):
    if row == col:
        tile = tile[:, :, [2, 1, 0]]

    if index % 3 == 0:
        tile = 255 - tile

    if index % 4 == 0:
        tile = cv2.rotate(tile, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif index % 4 == 1:
        tile = cv2.flip(tile, 1)
    elif index % 4 == 2:
        tile = cv2.rotate(tile, cv2.ROTATE_180)
    else:
        tile = cv2.flip(tile, 0)

    return tile.copy()


# Crop the largest centred square divisible by the grid size
def crop_image(image, g):
    height, width = image.shape[:2]
    side = (min(height, width) // g) * g

    if side == 0:
        raise ValueError("Image is too small for this grid size.")

    x = (width - side) // 2
    y = (height - side) // 2

    return image[y:y + side, x:x + side].copy()


# Split the image into tiles from top left to bottom right
def split_tiles(image, g):
    tile_size = image.shape[0] // g
    tiles = []

    for row in range(g):
        for col in range(g):
            y = row * tile_size
            x = col * tile_size
            tiles.append(
                image[y:y + tile_size, x:x + tile_size].copy()
            )

    return tiles


# Scramble the image using the given key
def scramble_image(original, g, key):
    tiles = split_tiles(original, g)
    total = g * g
    scrambled_tiles = [None] * total

    for index, tile in enumerate(tiles):
        row = index // g
        col = index % g

        changed = transform_tile(tile, index, row, col)
        destination = (index * key + g) % total
        scrambled_tiles[destination] = changed

    tile_size = original.shape[0] // g
    scrambled = np.zeros_like(original)

    for destination, tile in enumerate(scrambled_tiles):
        row = destination // g
        col = destination % g

        y = row * tile_size
        x = col * tile_size
        scrambled[y:y + tile_size, x:x + tile_size] = tile

    return scrambled


# Restore tiles to their original positions
def restore_image(scrambled, g, key):
    scrambled_tiles = split_tiles(scrambled, g)
    total = g * g
    tile_size = scrambled.shape[0] // g
    restored = np.zeros_like(scrambled)

    for index in range(total):
        row = index // g
        col = index % g

        source = (index * key + g) % total
        tile = scrambled_tiles[source]
        tile = restore_tile(tile, index, row, col)

        y = row * tile_size
        x = col * tile_size
        restored[y:y + tile_size, x:x + tile_size] = tile

    return restored


# Count tiles that match the original exactly
def count_correct_tiles(original, result, g):
    original_tiles = split_tiles(original, g)
    result_tiles = split_tiles(result, g)
    correct = 0

    for first, second in zip(original_tiles, result_tiles):
        if np.array_equal(first, second):
            correct += 1

    return correct


# Add a label to an image
def add_label(image, label):
    labelled = image.copy()

    cv2.rectangle(
        labelled,
        (0, 0),
        (labelled.shape[1], 40),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        labelled,
        label,
        (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    return labelled


def main():
    # Find photo.jpg in the same folder as this script
    folder = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(folder, "photo.jpg")

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Cannot read image: {image_path}\n"
            "Make sure photo.jpg is in the same folder."
        )

    # Ask for a valid grid size
    while True:
        try:
            g = int(input("Enter grid size (2-8): "))

            if 2 <= g <= 8:
                break

            print("Grid size must be between 2 and 8.")

        except ValueError:
            print("Please enter a whole number.")

    # Ask for a valid key
    while True:
        try:
            key = int(input("Enter key: "))

            if math.gcd(key, g * g) == 1:
                break

            print("Invalid key. gcd(key, grid size squared) must equal 1.")

        except ValueError:
            print("Please enter a whole number.")

    # Crop and scramble the image
    original = crop_image(image, g)
    scrambled = scramble_image(original, g, key)

    scrambled_path = os.path.join(folder, "scrambled.jpg")

    if not cv2.imwrite(scrambled_path, scrambled):
        raise OSError("Could not save scrambled.jpg.")

    # Load the saved scrambled image
    scrambled_from_file = cv2.imread(scrambled_path)

    if scrambled_from_file is None:
        raise OSError("Could not read scrambled.jpg.")

    # Restore the saved scrambled image using the original key
    restored = restore_image(scrambled_from_file, g, key)
    restored_path = os.path.join(folder, "restored.jpg")

    if not cv2.imwrite(restored_path, restored):
        raise OSError("Could not save restored.jpg.")

    # Compare the cropped original with the saved restored image
    restored_from_file = cv2.imread(restored_path)

    if restored_from_file is None:
        raise OSError("Could not read restored.jpg.")

    different_pixels = np.count_nonzero(
        np.any(original != restored_from_file, axis=2)
    )

    if different_pixels == 0:
        print("Restoration successful")
    else:
        print(f"Restoration failed: {different_pixels} pixels differ")

    # Find the next valid key after the entered key
    wrong_key = key + 1

    while math.gcd(wrong_key, g * g) != 1:
        wrong_key += 1

    # Restore the scrambled image using the next valid key
    wrong_image = restore_image(
        scrambled_from_file,
        g,
        wrong_key
    )

    correct_tiles = count_correct_tiles(original, wrong_image, g)
    total_tiles = g * g

    print(
        f"Wrong key {wrong_key}: "
        f"{correct_tiles} of {total_tiles} tiles correct."
    )

    # Display all four images in one 2 x 2 window
    images = [
        add_label(original, "Original"),
        add_label(scrambled_from_file, "Scrambled"),
        add_label(restored_from_file, "Restored"),
        add_label(wrong_image, "Wrong key")
    ]

    display_size = (400, 400)

    images = [
        cv2.resize(img, display_size)
        for img in images
    ]

    top = np.hstack((images[0], images[1]))
    bottom = np.hstack((images[2], images[3]))
    comparison = np.vstack((top, bottom))

    cv2.imshow("Image Tile Puzzle - Question 3", comparison)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()