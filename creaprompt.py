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
    
def select_random_line_from_collection():
    file_path = os.path.join(folder_path, "collection.txt")
    with open(file_path, "r", encoding="utf-8") as file:
      lines = file.readlines()
      readline = random.choice(lines).strip()
      return readline
    
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
                "Prompt_count":("INT", {"default": 1, "min": 1, "max": 1000}),
                "CreaPrompt_Collection": (["disabled"] + ["enabled"], {"default": "disabled"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 1125899906842624}),
            }
        }    
    def create_prompt(self, **kwargs):
        seed = kwargs.get("seed", 0)
        prompts_count = kwargs.get("Prompt_count", 0)
        concatenated_values = ""
        prompt_value = ""
        final_values = ""
        values = []
        values = [""] * len(name_of_files)
        if kwargs.get("CreaPrompt_Collection", 0) == "enabled":
          for c in range(prompts_count):  
            prompt_value = select_random_line_from_collection()  
            print(f"➡️CreaPrompt prompt: {prompt_value}")  
            final_values += prompt_value + "\n" 
            prompt_value = ""            
          final_values = final_values.strip()  
          print(f"➡️CreaPrompt Seed: {seed}")
          return (
            final_values,
            seed,
          )            
        else:         
         for c in range(prompts_count):
           for i, filename in enumerate(name_of_files):
              if kwargs.get(filename, 0) == "🎲random":
                     values[i] = select_random_line_from_csv_file(filename)
              else:      
                     values[i] = kwargs.get(filename, 0)
                     values[i] = values[i].strip()
           for value in values:
              if value != "disabled":
                     concatenated_values += value + ","
           print(f"➡️CreaPrompt prompt: {concatenated_values [:-1]}")
           final_values += concatenated_values [:-1] + "\n" 
           concatenated_values = ""
         final_values = final_values.strip()  
         print(f"➡️CreaPrompt Seed: {seed}")
         return (
            final_values,
            seed,
         )
        
class CreaPrompt_list:

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"Multi_prompts": ("STRING", {"multiline": True, "default": "body_text"}),
                             "prefix": ("STRING", {"multiline": True, "default": ""}),
                             "suffix": ("STRING", {"multiline": True, "default": ""}),
                            }
        }
    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("prompt", "prompt_debug",)
    OUTPUT_IS_LIST = (True, True, False)
    FUNCTION = "create_list"
    CATEGORY = "CreaPrompt"

    def create_list(self, Multi_prompts, prefix="", suffix=""):
        lines = Multi_prompts.split('\n')
        if prefix == "" and suffix == "":
              prompt_list_out = lines
        else:     
          if prefix != "" and suffix != "":
              prompt_list_out = [prefix + "," + line + "," + suffix for line in lines]
          else:   
             if prefix != "":
              prompt_list_out = [prefix + "," + line for line in lines]
             if suffix != "":   
              prompt_list_out = [line + "," + suffix for line in lines]
        if prefix == "" and suffix == "":
              prompt_list_debug = ["➡️" + line for line in lines]
        else:     
          if prefix != "" and suffix != "":
              prompt_list_debug = ["➡️" + prefix + "," + line + "," + suffix for line in lines]
          else:   
             if prefix != "":
              prompt_list_debug = ["➡️" + prefix + "," + line for line in lines]
             if suffix != "":   
              prompt_list_debug = ["➡️" + line + "," + suffix for line in lines]              
        debug_prompts = '\n'.join(prompt_list_debug)
        return (prompt_list_out, debug_prompts)       
        
NODE_CLASS_MAPPINGS = {
    "CreaPrompt": CreaPrompt, 
    "CreaPrompt List": CreaPrompt_list,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CreaPrompt": "CreaPrompt",
    "CreaPrompt List": "CreaPrompt Multi Prompts",
    "CSL": "Comma Separated List",
}
