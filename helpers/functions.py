import re
def process_USI(input):
    split_input = input.strip().split(":")
    dataset_name = split_input[1]
    file_name = split_input[2].split("/")[-1].split(".")[0]
    return dataset_name + ":" + file_name