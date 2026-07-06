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

# ============================================================================
# CreaPrompt Enhancer (imports lourds paresseux, rien n'est chargé au boot)
# ============================================================================

ENHANCER_PRESETS_PATH = os.path.join(script_directory, "enhancer_presets.json")

def load_enhancer_presets():
    try:
        with open(ENHANCER_PRESETS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ CreaPrompt Enhancer: presets load error: {e}")
        return {}

ENHANCER_PRESETS = load_enhancer_presets()
ENHANCER_PRESET_KEYS = list(ENHANCER_PRESETS.keys())

def enhancer_precision_options():
    import importlib.util
    opts = ["fp16", "bf16"]
    if importlib.util.find_spec("bitsandbytes") is not None:
        opts = ["int4", "int8"] + opts
    return opts

class CreaPromptEnhancerManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache = {}
        return cls._instance
    def get(self, key):
        return self.cache.get(key)
    def set(self, key, model, processor):
        self.cache[key] = (model, processor)
    def unload(self, key):
        if key in self.cache:
            import gc
            import torch
            model, processor = self.cache.pop(key)
            del model
            del processor
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print(f"🧹 CreaPrompt Enhancer: model '{key}' unloaded")

ENHANCER_MANAGER = CreaPromptEnhancerManager()

def enhancer_load_model(model_name, precision):
    key = f"{model_name}_{precision}"
    cached = ENHANCER_MANAGER.get(key)
    if cached:
        return cached

    import torch
    import folder_paths
    from huggingface_hub import snapshot_download
    from transformers import AutoProcessor
    try:
        from transformers import Qwen3VLForConditionalGeneration as MODEL_CLASS
    except ImportError:
        from transformers import Qwen2VLForConditionalGeneration as MODEL_CLASS

    models_dir = os.path.join(folder_paths.models_dir, "LLM")
    local_path = os.path.join(models_dir, model_name.split("/")[-1])

    if not os.path.isfile(os.path.join(local_path, "config.json")):
        print(f"⬇️ CreaPrompt Enhancer: downloading {model_name} to {local_path}...")
        snapshot_download(repo_id=model_name, local_dir=local_path)

    load_kwargs = {}
    if precision in ("int4", "int8"):
        from transformers import BitsAndBytesConfig
        if precision == "int4":
            load_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
        else:
            load_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        load_kwargs["device_map"] = "auto"
    else:
        load_kwargs["torch_dtype"] = torch.bfloat16 if precision == "bf16" else torch.float16

    print(f"⏳ CreaPrompt Enhancer: loading {model_name} ({precision})...")
    processor = AutoProcessor.from_pretrained(local_path, trust_remote_code=True)
    model = MODEL_CLASS.from_pretrained(
        local_path, trust_remote_code=True, low_cpu_mem_usage=True, **load_kwargs
    )
    if precision not in ("int4", "int8"):
        import comfy.model_management
        model.to(comfy.model_management.get_torch_device())

    ENHANCER_MANAGER.set(key, model, processor)
    print(f"✅ CreaPrompt Enhancer: model '{key}' loaded and cached")
    return model, processor

def enhancer_tensor_to_pil(tensor, max_size=1024, max_frames=None):
    from PIL import Image
    import numpy as np
    if tensor is None:
        return []
    total = tensor.shape[0]
    indices = range(total)
    if max_frames is not None and total > max_frames:
        step = total / max_frames
        indices = [int(i * step) for i in range(max_frames)]
    images = []
    for i in indices:
        img = Image.fromarray((tensor[i].cpu().numpy() * 255.0).astype(np.uint8))
        w, h = img.size
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        images.append(img)
    return images

def enhancer_describe_images(images, model_name, precision, seed):
    """Passe 1 : décrit chaque image individuellement (fiable pour les petits VL)."""
    descriptions = []
    for n, tensor in enumerate(images, 1):
        desc = enhancer_run(
            "Describe this image in detail, around 100 to 130 words: the main subject and its "
            "precise appearance (clothing, materials, textures, colors, pose or action) first, "
            "then the environment and background, the composition and framing, the lighting "
            "quality and direction, the color palette, the mood, and the medium or photographic "
            "style. Output only the description.",
            model_name, precision,
            "You are a precise visual analyst.",
            {"do_sample": False},
            384, seed + n,
            images=[tensor],
        )
        desc = desc.replace("\n", " ").strip()
        descriptions.append(desc)
        print(f"🖼️CreaPrompt image {n}: {desc}")
    return descriptions

def enhancer_merge_checklist(n_images, with_keywords):
    """Checklist en fin de message : contre le 'lost in the middle' des petits LLM."""
    items = "".join(
        f"- the main subject of Image {i}, plus elements of its style, lighting and mood\n"
        for i in range(1, n_images + 1)
    )
    if with_keywords:
        items += "- every keyword listed above\n"
    return (
        "\nMANDATORY CHECKLIST — your single output prompt MUST contain ALL of the "
        "following, blended into ONE coherent scene:\n" + items +
        "Before writing your final answer, silently verify that every item above is "
        "present in your prompt. Output only the prompt."
    )

def enhancer_run(prompt_text, model_name, precision, system_prompt, gen_params,
                 max_new_tokens, seed, images=None, video=None):
    import torch
    model, processor = enhancer_load_model(model_name, precision)

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    user_content = []
    if video is not None:
        frames = enhancer_tensor_to_pil(video, max_frames=32)
        user_content.append({"type": "video", "video": frames, "fps": 1.0})
    elif images:
        multi = len(images) > 1
        for n, tensor in enumerate(images, 1):
            if multi:
                user_content.append({"type": "text", "text": f"Image {n}:"})
            for img in enhancer_tensor_to_pil(tensor):
                user_content.append({"type": "image", "image": img})
    if prompt_text:
        user_content.append({"type": "text", "text": prompt_text})

    messages = [
        {"role": "system", "content": [{"type": "text", "text": system_prompt.strip()}]},
        {"role": "user", "content": user_content},
    ]

    inputs = processor.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True,
        return_dict=True, return_tensors="pt"
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    params = dict(gen_params or {})
    params.update({
        "max_new_tokens": max_new_tokens,
        "pad_token_id": processor.tokenizer.eos_token_id,
    })
    if params.get("do_sample") is False:
        # neutralise les defaults de generation_config.json (warning transformers en greedy)
        params.update({"temperature": None, "top_p": None, "top_k": None})

    with torch.inference_mode():
        generated_ids = model.generate(**inputs, **params)

    trimmed = [out[len(inp):] for inp, out in zip(inputs["input_ids"], generated_ids)]
    return processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=True
    )[0].strip()


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
        preset_options = ENHANCER_PRESET_KEYS + ["Your instruction"]
        precision_options = enhancer_precision_options()
        return {
            "required": {
                "__csv_json": ("STRING", {"multiline": True, "default": "{}", "input": False})
            },
            "optional": {
                "Prompt_count": ("INT", {"default": 1, "min": 1, "max": 1000}),
                "CreaPrompt_Collection": (["disabled"] + ["enabled"], {"default": "disabled"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 1125899906842624}),
                "Enhancer": (["disabled", "enabled"], {"default": "disabled"}),
                "Enhancer_model": ("STRING", {"default": "hfmaster/Qwen3-VL-4B"}),
                "Enhancer_precision": (precision_options, {"default": "fp16"}),
                "Enhancer_preset": (preset_options, {"default": preset_options[0]}),
                "Enhancer_instruction": ("STRING", {"multiline": True, "default": ""}),
                "Enhancer_max_tokens": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 64}),
                "Use_image": ("BOOLEAN", {"default": True}),
                "Use_image_plus_categories": ("BOOLEAN", {"default": False}),
                "Unload_after_generation": ("BOOLEAN", {"default": True}),
                "image": ("IMAGE",),
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "video": ("IMAGE",),
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

        # ===================== Enhancer =====================
        if kwargs.get("Enhancer", "disabled") == "enabled":
            if kwargs.get("Use_image", True):
                images = [t for t in (kwargs.get("image"), kwargs.get("image_2"), kwargs.get("image_3")) if t is not None]
                video = kwargs.get("video", None)
            else:
                images = []
                video = None
            model_name = kwargs.get("Enhancer_model", "hfmaster/Qwen3-VL-4B")
            precision = kwargs.get("Enhancer_precision", "int4")
            max_tokens = kwargs.get("Enhancer_max_tokens", 512)
            preset_name = kwargs.get("Enhancer_preset", "")
            preset = ENHANCER_PRESETS.get(preset_name, {})

            if preset_name == "Your instruction":
                system_prompt = kwargs.get("Enhancer_instruction", "").strip()
                gen_params = {"do_sample": True, "temperature": 0.7, "top_p": 0.8}
            else:
                system_prompt = preset.get("system_prompt", "")
                gen_params = preset.get("gen_params", {})

            try:
                if images and kwargs.get("Use_image_plus_categories", False):
                    # Mode image + texte : le visuel sert de référence, combiné aux fragments
                    # CSV/Collection, un appel LLM par ligne, format multi-lignes préservé
                    base_instruction = preset.get(
                        "image_text_instruction",
                        "You are given one or more images labeled Image 1, Image 2, etc. "
                        "Combine the main subject and the style, lighting and mood of EACH "
                        "labeled image with the following keywords into ONE single coherent "
                        "image generation prompt. Do not ignore any image. Output only the prompt."
                    )
                    # Deux passes systématiques : description(s) individuelle(s) fiable(s),
                    # puis fusion purement textuelle avec checklist — en un seul appel,
                    # l'attention du petit VL ignore l'image dès que les keywords sont denses
                    descs = enhancer_describe_images(images, model_name, precision, seed)
                    img_context = "Below are detailed descriptions of the labeled images.\n" + \
                        "\n".join(f"Image {n}: {d}" for n, d in enumerate(descs, 1))
                    checklist = enhancer_merge_checklist(len(images), with_keywords=True)
                    enhanced_lines = []
                    for idx, line in enumerate(final_values.split("\n")):
                        if not line.strip():
                            continue
                        text_input = f"{base_instruction}\n\n{img_context}\n\nKeywords: {line}\n{checklist}"
                        enhanced = enhancer_run(
                            text_input, model_name, precision, system_prompt,
                            gen_params, max_tokens, seed + idx
                        )
                        enhanced = enhanced.replace("\n", " ").strip() if enhanced else line
                        enhanced_lines.append(enhanced)
                        print(f"✨CreaPrompt enhanced: {enhanced}")
                    if enhanced_lines:
                        final_values = "\n".join(enhanced_lines)
                elif images or video is not None:
                    # Mode analyse visuelle : une seule description, le texte CSV est ignoré
                    if len(images) > 1:
                        # Deux passes : descriptions individuelles puis fusion textuelle
                        fusion_instruction = preset.get(
                            "fusion_instruction",
                            "Combine these images into ONE single image generation prompt: "
                            "take the main subject of each image and blend elements of the "
                            "style, lighting and mood of each into one coherent scene. "
                            "Output only the prompt."
                        )
                        descs = enhancer_describe_images(images, model_name, precision, seed)
                        img_context = "Below are detailed descriptions of the labeled images.\n" + \
                            "\n".join(f"Image {n}: {d}" for n, d in enumerate(descs, 1))
                        checklist = enhancer_merge_checklist(len(images), with_keywords=False)
                        enhanced = enhancer_run(
                            f"{fusion_instruction}\n\n{img_context}\n{checklist}",
                            model_name, precision, system_prompt,
                            gen_params, max_tokens, seed
                        )
                    else:
                        text_input = preset.get(
                            "image_instruction",
                            "Describe this image as a single detailed image generation prompt."
                        )
                        enhanced = enhancer_run(
                            text_input, model_name, precision, system_prompt,
                            gen_params, max_tokens, seed, images=images or None, video=video
                        )
                    if enhanced:
                        final_values = enhanced
                        print(f"✨CreaPrompt enhanced: {final_values}")
                else:
                    # Mode texte : un appel LLM par ligne, format multi-lignes préservé
                    enhanced_lines = []
                    for idx, line in enumerate(final_values.split("\n")):
                        if not line.strip():
                            continue
                        enhanced = enhancer_run(
                            line, model_name, precision, system_prompt,
                            gen_params, max_tokens, seed + idx
                        )
                        enhanced = enhanced.replace("\n", " ").strip() if enhanced else line
                        enhanced_lines.append(enhanced)
                        print(f"✨CreaPrompt enhanced: {enhanced}")
                    if enhanced_lines:
                        final_values = "\n".join(enhanced_lines)
            except Exception as e:
                print(f"⚠️ CreaPrompt Enhancer error, raw prompt returned: {e}")
            finally:
                if kwargs.get("Unload_after_generation", False):
                    ENHANCER_MANAGER.unload(f"{model_name}_{precision}")
        # ====================================================

        seeds_list = ", ".join(str(seed + i) for i in range(len(final_values.split("\n"))))
        print(f"➡️CreaPrompt Seed: {seeds_list}")
        return (final_values, seed)


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
                             "seed_base": ("INT", {"forceInput": True}),
                             "prefix": ("STRING", {"multiline": True, "default": ""}),
                             "suffix": ("STRING", {"multiline": True, "default": ""}),
                            }
        }
    RETURN_TYPES = ("STRING", "INT", "STRING",)
    RETURN_NAMES = ("prompt", "seed", "prompt_debug",)
    OUTPUT_IS_LIST = (True, True, False)
    FUNCTION = "create_list"
    CATEGORY = "CreaPrompt"

    def create_list(self, Multi_prompts, seed_base, prefix="", suffix=""):
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
        seed_list_out = [seed_base + i for i in range(len(prompt_list_out))]  
        print(f"➡️ Batch synchronisé : {len(prompt_list_out)} prompts / {len(seed_list_out)} seeds")        
        debug_prompts = '\n'.join(prompt_list_debug)
        return (prompt_list_out, seed_list_out, debug_prompts)       
        
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
