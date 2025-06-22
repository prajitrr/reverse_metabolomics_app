# import re
# def process_USI(input):
#     split_input = input.strip().split(":")
#     dataset_name = split_input[1]
#     file_name = split_input[2].split("/")[-1].split(".")[0]
#     return dataset_name + ":" + file_name

import re

def process_USI(usi: str) -> str:
    """
    Replicates the logic of the R ReDU_USI function.

    Args:
        usi: The input Universal Spectrum Identifier (USI) string.

    Returns:
        A transformed string containing the second and last parts of the
        processed USI, joined by a colon.
    """
    # In R: USI <- gsub("/", ":", USI)
    # Replaces all occurrences of "/" with ":"
    usi = usi.replace("/", ":")

    # In R: USI <- sub("\\.[^\\.]*$", "", USI)
    # Removes the last dot and any characters after it (like a file extension)
    usi = re.sub(r"\.[^.]*$", "", usi)

    # In R: parts <- unlist(strsplit(USI, ":"))
    # Splits the string into a list by the ":" delimiter
    parts = usi.split(":")

    # In R: combined <- paste(parts[2], parts[length(parts)], sep = ":")
    # Combines the second (index 1 in Python) and the last (index -1) parts
    # using a colon as a separator.
    combined = f"{parts[1]}:{parts[-1]}"

    return combined