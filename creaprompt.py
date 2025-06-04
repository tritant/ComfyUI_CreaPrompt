# ComfyUI version of CreaPrompt by Jicé Deb 
import random
import json
import os
import base64
from aiohttp import web
from server import PromptServer

script_directory = os.path.dirname(__file__)
folder_path = os.path.join(script_directory, "csv" )
folder_path_1 = os.path.join(script_directory, "csv1" )
folder_path_2 = os.path.join(script_directory, "csv2" )
folder_path_3 = os.path.join(script_directory, "csv3" )
folder_path_4 = os.path.join(script_directory, "csv+weight" )
CSV_FOLDER = os.path.join(os.path.dirname(__file__), "csv")
PRESET_FOLDER = os.path.join(os.path.dirname(__file__), "presets")
app = PromptServer.instance.app

async def preset_file(request):
    filename = request.match_info["filename"]
    path = os.path.join(PRESET_FOLDER, filename)
    if not os.path.isfile(path):
        return web.Response(status=404, text="Preset file not found.")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return web.Response(text=content)
    except Exception as e:
        return web.Response(status=500, text=f"Error reading preset: {e}")
        
async def save_preset(request):
    try:
        data = await request.json()
        name = data.get("name", "").strip()
        content = data.get("content", "").strip()

        if not name or len(name) < 2:
            return web.Response(status=400, text="Nom de preset invalide.")

        filename = os.path.join(PRESET_FOLDER, f"{name}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        #print(f"✅ Preset sauvegardé : {filename}")
        return web.Response(status=200, text="Preset saved.")
    except Exception as e:
        return web.Response(status=500, text=f"Erreur lors de la sauvegarde : {e}")

async def csv_list(request):
    #print("📥 csv_list endpoint hit")
    try:
        files = [f for f in os.listdir(CSV_FOLDER) if f.endswith(".csv")]
        return web.json_response(sorted(files))
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def csv_file(request):
    filename = request.match_info["filename"]
    path = os.path.join(CSV_FOLDER, filename)
    if not os.path.isfile(path):
        return web.Response(status=404, text="File not found.")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return web.Response(text=content)
    except Exception as e:
        return web.Response(status=500, text=f"Error reading file: {e}")
        
async def list_presets(request):
    try:
        files = [f for f in os.listdir(PRESET_FOLDER) if f.endswith(".txt")]
        return web.json_response(files)
    except Exception as e:
        return web.Response(status=500, text=f"Erreur lecture presets : {e}")
        
async def delete_preset(request):
    filename = request.match_info["filename"]
    path = os.path.join(PRESET_FOLDER, filename)
    if not os.path.isfile(path):
        return web.Response(status=404, text="Preset file not found.")
    try:
        os.remove(path)
        #print(f"🗑️ Preset supprimé : {path}")
        return web.Response(text="Preset deleted.")
    except Exception as e:
        return web.Response(status=500, text=f"Error deleting preset: {e}")
                
app.router.add_get("/custom_nodes/creaprompt/csv_list", csv_list)
app.router.add_get("/custom_nodes/creaprompt/csv/{filename}", csv_file)
app.router.add_get("/custom_nodes/creaprompt/presets/{filename}", preset_file)
app.router.add_post("/custom_nodes/creaprompt/save_preset", save_preset)
app.router.add_get("/custom_nodes/creaprompt/presets_list", list_presets)
app.router.add_delete("/custom_nodes/creaprompt/delete_preset/{filename}", delete_preset)
print("✅ creaprompt_api registering endpoints")

def getfilename(folder):
    name = []
    for filename in os.listdir(folder):
        if filename.endswith(".csv"):
           name.append(filename[3:-4])
    return name
    
def select_random_line_from_collection():
    file_path = os.path.join(folder_path, "collection.txt")
    with open(file_path, "r", encoding="utf-8") as file:
      lines = file.readlines()
      readline = random.choice(lines).strip()
      return readline
    
def select_random_line_from_csv_file(file, folder):
    chosen_lines = []
    for filename in os.listdir(folder):
        if filename.endswith(".csv") and filename[3:-4] == file:
            file_path = os.path.join(folder, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    chosen_lines.append(random.choice(lines).strip())
    lines_chosed = "".join(chosen_lines)
    return lines_chosed

class CreaPrompt_0:

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
    def IS_CHANGED(self, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "__csv_json": ("STRING", {"multiline": True, "default": "{}", "input": False})
            },
            "optional": {
                "Prompt_count": ("INT", {"default": 1, "min": 1, "max": 1000}),
                "CreaPrompt_Collection": (["disabled"] + ["enabled"], {"default": "disabled"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 1125899906842624}),
            }
        }

    def create_prompt(self, **kwargs):
        name_of_files = getfilename(folder_path)
        seed = kwargs.get("seed", 0)
        prompts_count = kwargs.get("Prompt_count", 0)
        concatenated_values = ""
        prompt_value = ""
        final_values = ""
        values = []
        values = [""] * len(name_of_files)

        # 🔎 Debug
        #print("📦 kwargs:", json.dumps(kwargs, indent=2))

        dynamic_values = json.loads(kwargs.get("__csv_json", "{}"))
        #print("🧩 dynamic_values:", json.dumps(dynamic_values, indent=2))

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
                    val = dynamic_values.get(filename, "disabled")
                    if val == "🎲random":
                        values[i] = select_random_line_from_csv_file(filename, folder_path)
                    else:      
                        values[i] = val.strip()
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
    def IS_CHANGED(self, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        required = {}
        for filename in sorted(os.listdir(folder_path)):
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
        name_of_files = getfilename(folder_path)
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
                     values[i] = select_random_line_from_csv_file(filename, folder_path)
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
         
class CreaPrompt_1:

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
    def IS_CHANGED(self, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        required = {}
        for filename in os.listdir(folder_path_1):
              if filename.endswith(".csv"):
                 file_path = os.path.join(folder_path_1, filename)
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
        name_of_files = getfilename(folder_path_1)
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
                     values[i] = select_random_line_from_csv_file(filename, folder_path_1)
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

class CreaPrompt_2:

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
    def IS_CHANGED(self, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        required = {}
        for filename in os.listdir(folder_path_2):
              if filename.endswith(".csv"):
                 file_path = os.path.join(folder_path_2, filename)
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
        name_of_files = getfilename(folder_path_2)
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
                     values[i] = select_random_line_from_csv_file(filename, folder_path_2)
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

class CreaPrompt_3:

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
    def IS_CHANGED(self, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        required = {}
        for filename in os.listdir(folder_path_3):
              if filename.endswith(".csv"):
                 file_path = os.path.join(folder_path_3, filename)
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
        name_of_files = getfilename(folder_path_3)
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
                     values[i] = select_random_line_from_csv_file(filename, folder_path_3)
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

class CreaPrompt_4:

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
    def IS_CHANGED(self, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        required = {}
        for filename in os.listdir(folder_path_4):
              if filename.endswith(".csv"):
                 file_path = os.path.join(folder_path_4, filename)
                 lines = []
                 with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    required[filename [3:-4]] = (["disabled"] + ["🎲random"] + lines, {"default": "disabled"})
                    required[filename [3:-4] + ": Weight"] = ("FLOAT", {"default": 1, "min": -3, "max": 3})
        return {
            "required": required,
            "optional": {
                "Prompt_count":("INT", {"default": 1, "min": 1, "max": 1000}),
                "CreaPrompt_Collection": (["disabled"] + ["enabled"], {"default": "disabled"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 1125899906842624}),
            }
        }    
    def create_prompt(self, **kwargs):
        name_of_files = getfilename(folder_path_4)
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
                     values[i] = select_random_line_from_csv_file(filename, folder_path_4)
                     if kwargs.get(filename + ": Weight", 0) != 0 and kwargs.get(filename + ": Weight", 0) != 1: 
                        values[i] = f"({values[i]}:{kwargs.get(filename + ': Weight', 0):.1f})"
              else:      
                     values[i] = kwargs.get(filename, 0)
                     values[i] = values[i].strip()
                     if kwargs.get(filename + ": Weight", 0) != 0 and kwargs.get(filename + ": Weight", 0) != 1: 
                          values[i] = f"({values[i]}:{kwargs.get(filename + ': Weight', 0):.1f})"
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
        Multi_prompts = Multi_prompts.strip()
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
    "CreaPrompt_0": CreaPrompt_0,
    "CreaPrompt": CreaPrompt, 
    "CreaPrompt_1": CreaPrompt_1,
    "CreaPrompt_2": CreaPrompt_2,
    "CreaPrompt_3": CreaPrompt_3,
    "CreaPrompt_4": CreaPrompt_4,
    "CreaPrompt List": CreaPrompt_list,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CreaPrompt_0": "CreaPrompt Dynamic node",
    "CreaPrompt": "CreaPrompt complete node",
    "CreaPrompt_1": "CreaPrompt node 1",
    "CreaPrompt_2": "CreaPrompt node 2",
    "CreaPrompt_3": "CreaPrompt node 3",
    "CreaPrompt_4": "CreaPrompt node with weight",
    "CreaPrompt List": "CreaPrompt Multi Prompts",
    "CSL": "Comma Separated List",
}
