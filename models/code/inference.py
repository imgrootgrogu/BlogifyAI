import os
import json
import torch
import base64
import io
from PIL import Image
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
from safetensors.torch import load_file

def model_fn(model_dir):
    """
    Load and initialize the model for inference.
    
    Args:
        model_dir (str): Directory where model files are stored
    
    Returns:
        dict: Initialized pipelines and model-related resources
    """
  
    MODEL_DIR = "./weights"  
    MODEL_PATH = os.path.join(MODEL_DIR, "base_model.safetensors")
    VAE_PATH = os.path.join(MODEL_DIR, "vae.safetensors")
    LORA1_PATH = os.path.join(MODEL_DIR, "lora1.safetensors")
    LORA2_PATH = os.path.join(MODEL_DIR, "lora2.safetensors")

 
    text2img_pipeline = StableDiffusionPipeline.from_single_file(
        MODEL_PATH, 
        torch_dtype=torch.float16  
    ).to("cuda") 
    
   
    img2img_pipeline = StableDiffusionImg2ImgPipeline.from_single_file(
        MODEL_PATH, 
        torch_dtype=torch.float16
    ).to("cuda")
    
  
    vae = load_file(VAE_PATH)
    text2img_pipeline.vae.load_state_dict(vae, strict=False)
    img2img_pipeline.vae.load_state_dict(vae, strict=False)
    
   
    return {
        "text2img": text2img_pipeline,
        "img2img": img2img_pipeline,
        "lora1_path": LORA1_PATH,
        "lora2_path": LORA2_PATH
    }

def input_fn(request_body, request_content_type):
    """
    Parse and validate incoming request data.
    
    Args:
        request_body (str): Raw request payload
        request_content_type (str): Content type of the request
    
    Returns:
        dict: Parsed and validated input data
    """
    if request_content_type == 'application/json':
        try:
            input_data = json.loads(request_body)
            
          
            if "mode" not in input_data:
                input_data["mode"] = "text2img"
            
            defaults = {
                "prompt": "",
                "negative_prompt": "",
                "num_inference_steps": 50,
                "guidance_scale": 7.5,
                "height": 1024,
                "width": 1024,
                "seed": 42,
                "lora": None,
                "strength": 0.9
            }
            
        
            for key, default_value in defaults.items():
                input_data.setdefault(key, default_value)
            
            return input_data
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON input")
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")

def predict_fn(input_data, model):
    """
    Generate image based on input parameters.
    
    Args:
        input_data (dict): Parsed input parameters
        model (dict): Loaded model resources
    
    Returns:
        dict: Generated image in base64 format
    """

    mode = input_data["mode"]
    prompt = input_data["prompt"]
    negative_prompt = input_data["negative_prompt"]
    num_inference_steps = input_data["num_inference_steps"]
    guidance_scale = input_data["guidance_scale"]
    height = input_data["height"]
    width = input_data["width"]
    seed = input_data["seed"]
    lora = input_data["lora"]
    strength = input_data["strength"]
    
  
    pipeline = model["text2img"] if mode == "text2img" else model["img2img"]
    
    if lora:
        lora_path = model["lora1_path"] if lora == "lingsha" else model["lora2_path"]
        pipeline.load_lora_weights(lora_path, weight=1.0)
    
   
    generator = torch.manual_seed(seed)
    
 
    if mode == "text2img":
        result = pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            height=height,
            width=width,
            generator=generator,
        )
        image = result.images[0]
    

    else:
     
        if "input_image" not in input_data:
            raise ValueError("Input image is required for img2img mode")
        
   
        input_image_data = base64.b64decode(input_data["input_image"])
        input_image = Image.open(io.BytesIO(input_image_data))
        
        result = pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            image=input_image,
            strength=strength,
            guidance_scale=guidance_scale,
            height=height,
            width=width,
            generator=generator,
        )
        image = result.images[0]
    
   
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {"image": image_base64}

def output_fn(prediction, response_content_type):
    """
    Format the output for the response.
    
    Args:
        prediction (dict): Generated image data
        response_content_type (str): Desired response content type
    
    Returns:
        str: Formatted response payload
    """
    if response_content_type == 'application/json':
        return json.dumps(prediction)
    raise ValueError(f"Unsupported content type: {response_content_type}")
