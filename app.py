import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from google import genai

st.set_page_config(page_title="AI Drawing Calculator", page_icon="🧮", layout="wide")
st.title("🧮 AI Drawing Calculator")

# Sidebar setup for API key and brush controls
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password", help="Get a free key from Google AI Studio")
    stroke_width = st.slider("Pen Thickness", 1, 15, 4)
    stroke_color = st.color_picker("Pen Color", "#000000")
    bg_color = st.color_picker("Board Color", "#FFFFFF")

# Main interface layout
col1, col2 = st.columns([3, 2])
with col1:
    canvas_result = st_canvas(
        stroke_width=stroke_width, stroke_color=stroke_color,
        background_color=bg_color, height=420, width=650,
        drawing_mode="freedraw", return_image_data=True, key="math_canvas"
    )

with col2:
    extra_notes = st.text_input("Optional hint (e.g., 'Solve for x'):")
    if st.button("Solve Problem", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        elif canvas_result.image_data is None:
            st.warning("Please draw a problem on the canvas first.")
        else:
            with st.spinner("Reading handwriting and solving..."):
                img = Image.fromarray(canvas_result.image_data.astype("uint8"), "RGBA")
                background = Image.new("RGBA", img.size, bg_color)
                final_img = Image.alpha_composite(background, img).convert("RGB")
                
                client = genai.Client(api_key=api_key)
                prompt = f"Transcribe this handwritten problem in LaTeX and solve it step-by-step. Hint: {extra_notes}"
                response = client.models.generate_content(model="gemini-2.5-flash", contents=[final_img, prompt])
                st.markdown(response.text)
