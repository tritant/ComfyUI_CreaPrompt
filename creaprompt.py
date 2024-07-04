# ComfyUI version of CreaPrompt by Jicé Deb 
import random
import json
import os

script_directory = os.path.dirname(__file__)
os.chdir(script_directory)
folder_path = os.path.join(script_directory, "csv" )

def getfilename():
    name = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
           name.append(filename[3:-4])
    return name
    
def select_random_line_from_csv_file(file):
    chosen_lines = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv") and filename[3:-4] == file:
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                if lines:
                    chosen_lines.append(random.choice(lines).strip())
    lines_chosed = "".join(chosen_lines)
    return lines_chosed
    
name_of_files = getfilename()

class CreaPrompt:
    RETURN_TYPES = (
        "STRING",
        "INT",
    )
    RETURN_NAMES = (
        "prompt",
        "seed",
    )
    FUNCTION = "create_prompt"
    CATEGORY = "CreaPrompt"

    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    @classmethod
    def IS_CHANGED(cls):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        required = {}
        for filename in os.listdir(folder_path):
              if filename.endswith(".csv"):
                 file_path = os.path.join(folder_path, filename)
                 lines = []
                 with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    required[filename [3:-4]] = (["disabled"] + ["🎲random"] + lines, {"default": "disabled"})
        return {
            "required": required,
            "optional": {
                "seed": (
                    "INT",
                    {"default": 0, "min": 0, "max": 1125899906842624},
                ),
            },
        }    
    def create_prompt(self, **kwargs):
        seed = kwargs.get("seed", 0)
        concatenated_values = ""
        values = []
        values = [""] * len(name_of_files)
        for i, filename in enumerate(name_of_files):
             if kwargs.get(filename, 0) == "🎲random":
                    values[i] = select_random_line_from_csv_file(filename)
             else:      
                    values[i] = kwargs.get(filename, 0)
                    values[i] = values[i].strip()
        for value in values:
             if value != "disabled":
                    concatenated_values += value + ","
        print(f"CreaPrompt Seed  : {seed}")
        final_prompt = concatenated_values
        print(f"CreaPrompt prompt: {final_prompt}")
        return (
            final_prompt,
            seed,
        )
NODE_CLASS_MAPPINGS = {
    "CreaPrompt": CreaPrompt,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CreaPrompt": "CreaPrompt",
    "CSL": "Comma Separated List",
}
