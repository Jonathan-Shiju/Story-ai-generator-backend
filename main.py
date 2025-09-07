from fastapi import FastAPI, HTTPException
import sys
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
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
from crewai import llm

# Define LoRA paths
LORA_PATHS = {
    "lego": "../Stable_Diffusion_lora/Lego.safetensors",
    "oil": "../Stable_Diffusion_lora/Oil.safetensors",
    "manga": "../Stable_Diffusion_lora/Manga.safetensors",
    "anime": "../Stable_Diffusion_lora/animescreencap_xl.safetensors",
    "sketch": "../Stable_Diffusion_lora/Sketch.safetensors",
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
            lora_adapters[style] = path
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
    def run_story_flow():
        story_flow = StoryFlow()
        story_flow.kickoff(inputs={
            "user_story": payload.prompt,
            "user_genre": payload.genre,
            "user_tone": payload.tone,
            "user_audience": "kids"
        })
        return story_flow
    
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        story_flow = await loop.run_in_executor(executor, run_story_flow)
    
    if not story_flow.state.story:
        raise HTTPException(status_code=500, detail="Story generation failed.")
        
    return story_flow.state.story


@app.post("/api/stories/refine")
async def refine_story(payload: RefineStoryPayload):
    """Refines an existing story using Gemini 2.0 Flash Lite via CrewAI."""
    try:
        prompt = f"Refine this story for kids: {payload.story}\nPrompt: {payload.prompt}"
        refined_story = await llm.chat(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that refines children's stories."},
                {"role": "user", "content": prompt}
            ],
            model="gemini-2.0-flash-lite"
        )
        return {"refined_story": refined_story}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM refinement failed: {str(e)}")

@app.post("/api/stories/get_scenes")
async def get_scenes(payload: GetScenesPayload):
    """Generates 5 distinct scenes from a story outline and creates images for them."""
    def run_scenes_flow():
        scenes_flow = ScenesFlow()
        scenes_flow.kickoff(inputs={"story": str(payload.story)})
        return scenes_flow
    
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        scenes_flow = await loop.run_in_executor(executor, run_scenes_flow)
    
    if not scenes_flow.state.scenes:
        raise HTTPException(status_code=500, detail="Scene generation failed.")

    scenes_dict = scenes_flow.state.scenes.dict()

    art_style = payload.artStyle.lower()
    lora_path = lora_adapters.get(art_style)
    if not lora_path:
        raise HTTPException(status_code=400, detail=f"Art style '{art_style}' not supported.")
    
    # Load the specific LoRA adapter for this request
    pipe.load_lora_weights(lora_path)

    formatted_scenes = {}
    try:
        for key, scene_prompt in scenes_dict.items():
            if not scene_prompt:
                formatted_scenes[key] = {"PIL": None, "Text": scene_prompt}
                continue

            image = pipe(prompt=scene_prompt).images[0]
            
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

            formatted_scenes[key] = {"PIL": img_str, "Text": scene_prompt}
    finally:
        # Unload the adapter in a finally block to ensure it's always unloaded
        # This is the key difference and an improvement from the original code
        pipe.unload_lora_weights()
    
    return formatted_scenes