from fastapi import FastAPI, HTTPException
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'story-generator', 'story_creator_flow', 'src'))
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import torch
from diffusers import StableDiffusionXLPipeline
from PIL import Image
import io
import base64
from story_creator_flow.main import StoryFlow, ScenesFlow
import os

# Define LoRA paths
LORA_PATHS = {
    "lego": "./Stable_Diffusion_lora/Lego.safetensors",
    "oil": "./Stable_Diffusion_lora/oil.safetensors",
    "manga": "./Stable_Diffusion_lora/Manga.safetensors",
    "anime": "./Stable_Diffusion_lora/animescreencap_xl.safetensors",
    "sketch": "./Stable_Diffusion_lora/Sketch.safetensors",
}

app = FastAPI(title="CrewAI Story Generator API")

# Initialize the pipeline once per worker
@app.on_event("startup")
def startup_event():
    global pipe
    global lora_adapters

    print("Loading SDXL pipeline and LoRA weights...")

    model_id = "stabilityai/stable-diffusion-xl-base-1.0"
    pipe = StableDiffusionXLPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        use_safetensors=True
    ).to("cuda" if torch.cuda.is_available() else "cpu")

    lora_adapters = {}
    for style, path in LORA_PATHS.items():
        if os.path.exists(path):
            pipe.load_lora_weights(path, adapter_name=style)
            lora_adapters[style] = True
        else:
            print(f"Warning: LoRA file not found at {path}. Skipping '{style}' style.")

    print("Startup complete. Ready to serve requests.")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateStoryPayload(BaseModel):
    prompt: str
    genre: str
    tone: str

class RefineStoryPayload(BaseModel):
    prompt: str
    story: Dict[str, Any]

class GetScenesPayload(BaseModel):
    story: Dict[str, Any]
    artStyle: str

@app.get("/")
async def root():
    return {"message": "API is up and running"}

@app.post("/api/stories/generate")
async def generate_story(payload: GenerateStoryPayload):
    """Generates a story outline based on a prompt, genre, and tone."""
    story_flow = StoryFlow()
    story_flow.kickoff(inputs={
        "user_story": payload.prompt,
        "user_genre": payload.genre,
        "user_tone": payload.tone,
        "user_audience": payload.artStyle
    })
    
    if not story_flow.state.story:
        raise HTTPException(status_code=500, detail="Story generation failed.")
        
    return story_flow.state.story

@app.post("/api/stories/refine")
async def refine_story(payload: RefineStoryPayload):
    """Refines an existing story based on a new prompt."""
    story_flow = StoryFlow()
    story_flow.kickoff(inputs={
        "user_story": payload.prompt,
        "user_genre": payload.story.get("genre", "fantasy"),
        "user_tone": payload.story.get("tone", "lighthearted"),
        "user_audience": payload.story.get("artStyle", "general")
    })

    if not story_flow.state.story:
        raise HTTPException(status_code=500, detail="Story refinement failed.")

    return story_flow.state.story

@app.post("/api/stories/get_scenes")
async def get_scenes(payload: GetScenesPayload):
    """Generates 5 distinct scenes from a story outline and creates images for them."""
    scenes_flow = ScenesFlow()
    scenes_flow.kickoff(inputs={"story": str(payload.story)})
    
    if not scenes_flow.state.scenes:
        raise HTTPException(status_code=500, detail="Scene generation failed.")

    scenes_dict = scenes_flow.state.scenes.dict()

    art_style = payload.artStyle.lower()
    if art_style not in lora_adapters:
        raise HTTPException(status_code=400, detail=f"Art style '{art_style}' not supported.")
    
    # Set the LoRA adapter for the current request
    pipe.set_adapters(art_style)

    formatted_scenes = {}
    for key, scene_prompt in scenes_dict.items():
        if not scene_prompt:
            formatted_scenes[key] = {"PIL": None, "Text": scene_prompt}
            continue

        image = pipe(prompt=scene_prompt).images[0]
        
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        formatted_scenes[key] = {"PIL": img_str, "Text": scene_prompt}
    
    # Unload the adapter after the request is complete
    pipe.set_adapters([])
    
    return formatted_scenes