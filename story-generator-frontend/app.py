import streamlit as st
import requests
import base64
import io
from PIL import Image
from fpdf import FPDF
from fpdf.enums import Align
import json

# --- Configuration ---
API_BASE_URL = "https://34606e239500.ngrok-free.app" # Replace with your actual backend URL if different
GENERATE_STORY_URL = f"{API_BASE_URL}/api/stories/generate"
REFINE_STORY_URL = f"{API_BASE_URL}/api/stories/refine"
GET_SCENES_URL = f"{API_BASE_URL}/api/stories/get_scenes"

# --- PDF Generation Function ---
def create_pdf(scenes_data: dict, story_title: str):
    """Generates a PDF from the story scenes."""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Add Title Page
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 24)
        pdf.multi_cell(w=0, h=20, txt=f"Your Story:\n{story_title}", align='C')

        # Add Scene Pages
        for scene_key, scene_content in sorted(scenes_data.items()):
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            
            # Scene Title (e.g., "Scene 1")
            scene_number = scene_key.split('_')[-1]
            pdf.cell(w=0, h=10, txt=f"Scene {scene_number}", ln=1, align='C')
            pdf.ln(10)

            # Handle and place the image
            img_str = scene_content.get("PIL")
            if img_str:
                try:
                    img_data = base64.b64decode(img_str)
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Save image to a temporary file for better compatibility
                    temp_img_path = f"temp_scene_{scene_number}.png"
                    img.save(temp_img_path, format="PNG")
                    
                    # Calculate dimensions
                    page_width = pdf.w - 2 * pdf.l_margin
                    img_width, img_height = img.size
                    ratio = img_height / img_width if img_width > 0 else 0
                    new_width = page_width
                    new_height = new_width * ratio
                    
                    # Add image to PDF
                    x_pos = (pdf.w - new_width) / 2
                    pdf.image(temp_img_path, x=x_pos, w=new_width)
                    pdf.ln(10)  # Add some space after the image
                    
                    # Clean up temporary file
                    import os
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
                        
                except Exception as e:
                    st.warning(f"Could not process image for Scene {scene_number}: {e}")
                    # Continue with the text even if image fails

            # Handle and place the text
            pdf.set_font("Helvetica", "", 12)
            text = scene_content.get("Text")
            if text:
                # Handle potential encoding issues
                text = text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(w=0, h=10, txt=text, align='J')
        
        # Use BytesIO to get binary PDF data
        pdf_data = io.BytesIO()
        pdf.output(pdf_data)
        return pdf_data.getvalue()
    
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None


# --- UI Helper Functions ---
def display_story(story_data):
    """
    Renders the story in a readable format.
    Handles both structured dictionary and plain string inputs.
    """
    if isinstance(story_data, dict):
        st.markdown(f"### {story_data.get('title', 'Your Story')}")
        st.markdown(f"**Logline:** *{story_data.get('logline', 'N/A')}*")
        
        st.markdown("---")
        
        for i in range(1, 4):
            act_key = f"act_{i}"
            if act_key in story_data:
                st.markdown(f"**Act {i}:** {story_data[act_key]}")

        st.markdown("---")
        # Check for a full story text within the dictionary
        if isinstance(story_data.get('story'), str):
            st.markdown(story_data['story'])

    elif isinstance(story_data, str):
        # If it's just a string, display the whole text
        st.markdown("### Your Story")
        st.markdown("---")
        st.write(story_data)
    else:
        st.warning("The story format received from the backend is unrecognized.")
        st.json(story_data)


# --- Main Application Logic ---
st.set_page_config(layout="wide", page_title="AI Story Generator")

st.title("🎨 AI Story & Scene Generator 🎬")
st.markdown("Create a unique story, refine it, and bring it to life with AI-generated images for each scene.")

if 'stage' not in st.session_state:
    st.session_state.stage = 'generate'
if 'story_data' not in st.session_state:
    st.session_state.story_data = None
if 'scenes_data' not in st.session_state:
    st.session_state.scenes_data = None

# --- STAGE 1: Generate Story ---
if st.session_state.stage == 'generate':
    st.header("Step 1: Create Your Story")
    with st.form("story_form"):
        prompt = st.text_area("Enter a brief for your story:", "A lost robot trying to find its way home in a fantasy forest.")
        genre = st.selectbox("Choose a genre:", ["Fantasy", "Sci-Fi", "Mystery", "Adventure", "Fairy Tale"])
        tone = st.selectbox("Choose a tone:", ["Whimsical", "Serious", "Humorous", "Suspenseful", "Heartwarming"])
        
        submitted = st.form_submit_button("Generate Story", type="primary")

    if submitted:
        # Clear any debug info from previous runs
        if 'debug_info' in st.session_state:
            del st.session_state.debug_info

        with st.spinner("The AI is writing your story..."):
            try:
                payload = {"prompt": prompt, "genre": genre, "tone": tone}
                response = requests.post(GENERATE_STORY_URL, json=payload, timeout=300)
                
                st.session_state.debug_info = {
                    "status_code": response.status_code,
                    "response_text": response.text
                }

                response.raise_for_status()
                
                try:
                    st.session_state.story_data = response.json()
                except json.JSONDecodeError:
                    st.session_state.story_data = response.text
                
                if not st.session_state.story_data:
                    st.error("Backend returned a successful status but the response body was empty. Please check the backend logs.")
                else:
                    st.session_state.stage = 'refine_and_visualize'
                    st.rerun()

            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to the backend: {e}")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Display debug info if it exists
if 'debug_info' in st.session_state and st.session_state.stage == 'generate':
    with st.expander("Last Backend Response (for debugging)"):
        st.info(f"Backend Response Status Code: {st.session_state.debug_info['status_code']}")
        st.text("Raw Backend Response:")
        st.code(st.session_state.debug_info['response_text'], language='text')

# --- STAGE 2: Refine and Visualize ---
elif st.session_state.stage == 'refine_and_visualize':
    st.header("Step 2: Review, Refine, and Visualize")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("Your Generated Story")
        if st.session_state.story_data:
            display_story(st.session_state.story_data)
        else:
            st.warning("No story generated yet. Go back to Step 1.")
    
    with col2:
        st.subheader("Refine Your Story (Optional)")
        with st.form("refine_form"):
            refine_prompt = st.text_area("Enter a prompt to edit or change the story:", "Make the main character a brave squirrel instead of a robot.")
            refine_submitted = st.form_submit_button("Refine Story")

        if refine_submitted:
            with st.spinner("Refining the story with your suggestions..."):
                try:
                    payload = {"prompt": refine_prompt, "story": st.session_state.story_data}
                    response = requests.post(REFINE_STORY_URL, json=payload, timeout=300)
                    response.raise_for_status()
                    refined_story_response = response.json()
                    
                    st.session_state.story_data = refined_story_response.get("refined_story", st.session_state.story_data)

                    st.success("Story refined!")
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to the backend: {e}")
                except Exception as e:
                    st.error(f"An error occurred during refinement: {e}")

        st.markdown("---")
        st.subheader("Create Visual Scenes")
        with st.form("scenes_form"):
            art_style = st.selectbox("Choose an art style:", ["oil", "lego", "sketch", "anime", "manga"])
            scenes_submitted = st.form_submit_button("Generate 5 Scenes", type="primary")

        if scenes_submitted:
            with st.spinner("Generating scenes and creating images... This might take a few moments."):
                try:
                    payload = {"story": st.session_state.story_data, "artStyle": art_style}
                    response = requests.post(GET_SCENES_URL, json=payload, timeout=600)
                    response.raise_for_status()
                    st.session_state.scenes_data = response.json()
                    st.session_state.stage = 'download'
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to the backend: {e}")
                except Exception as e:
                    st.error(f"An error occurred during scene generation: {e}")

# --- STAGE 3: Download ---
elif st.session_state.stage == 'download':
    st.header("Step 3: Your Story Scenes")
    
    if st.session_state.scenes_data:
        st.markdown("Here are the scenes for your story, brought to life! Review them below, and then choose an option.")
        st.markdown("---")
        
        # --- Scene Viewer ---
        for key, scene in sorted(st.session_state.scenes_data.items()):
            scene_number = key.split('_')[-1]
            st.subheader(f"Scene {scene_number}")
            if scene.get("PIL"):
                try:
                    img_data = base64.b64decode(scene["PIL"])
                    # --- FIX: Use use_container_width instead of deprecated use_column_width ---
                    st.image(img_data, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not display image for Scene {scene_number}: {e}")
            
            if scene.get("Text"):
                st.markdown(f"> {scene['Text']}")
            st.markdown("---")

        # --- Actions at the bottom ---
        st.subheader("What's next?")

        story_title = "My AI Story"
        if isinstance(st.session_state.story_data, dict):
            story_title = st.session_state.story_data.get('title', 'My AI Story')
        elif isinstance(st.session_state.story_data, str):
             # Try to extract a title from the first line of the string
            try:
                first_line = st.session_state.story_data.strip().split('\n')[0]
                # A simple heuristic: if it looks like a title, use it.
                if len(first_line) < 70 and not first_line.endswith('.'):
                    story_title = first_line.strip("# ")
            except IndexError:
                pass


        pdf_bytes = create_pdf(st.session_state.scenes_data, story_title)
        if pdf_bytes:
            story_title_slug = "".join(x for x in story_title if x.isalnum() and x.isascii()).strip() or "GeneratedStory"
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Download Story as PDF",
                    data=pdf_bytes,
                    file_name=f"{story_title_slug}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
        else:
            st.error("Failed to generate PDF. Please try again.")
            
        with col2:
            if st.button("Start Over", use_container_width=True):
                st.session_state.clear()
                st.rerun()

    else:
        st.warning("No scenes were generated. Please go back and try again.")
        if st.button("Start Over"):
            st.session_state.clear()
            st.rerun()

