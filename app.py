import base64
import io
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from google import genai

st.set_page_config(page_title="AI Drawing Calculator", page_icon="🧮", layout="wide")
st.title("🧮 AI Drawing Calculator")

with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password", help="Get a free key from Google AI Studio")
    pen_size = st.slider("Pen Thickness", 2, 12, 4)

# Built-in HTML5 Canvas (no external Streamlit component needed)
canvas_html = f"""
<div style="font-family: sans-serif;">
  <canvas id="board" width="650" height="400" style="border: 2px solid #ccc; border-radius: 8px; background: white; cursor: crosshair; touch-action: none;"></canvas>
  <div style="margin-top: 8px; display: flex; gap: 10px;">
    <button onclick="clearCanvas()" style="padding: 6px 14px; border-radius: 6px; border: 1px solid #ccc; cursor: pointer;">Clear Board</button>
    <button onclick="copyImage()" style="padding: 6px 14px; border-radius: 6px; border: none; background: #ff4b4b; color: white; cursor: pointer;">Copy Drawing</button>
    <span id="status" style="align-self: center; font-size: 13px; color: green;"></span>
  </div>
</div>
<script>
  const canvas = document.getElementById('board');
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = "white";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.lineWidth = {pen_size};
  ctx.lineCap = 'round';
  ctx.strokeStyle = 'black';
  let drawing = false;

  const getPos = (e) => {{
    const rect = canvas.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    return [clientX - rect.left, clientY - rect.top];
  }};

  const start = (e) => {{ drawing = true; ctx.beginPath(); ctx.moveTo(...getPos(e)); }};
  const draw = (e) => {{ if (!drawing) return; e.preventDefault(); ctx.lineTo(...getPos(e)); ctx.stroke(); }};
  const stop = () => {{ drawing = false; }};

  canvas.addEventListener('mousedown', start);
  canvas.addEventListener('mousemove', draw);
  canvas.addEventListener('mouseup', stop);
  canvas.addEventListener('touchstart', start);
  canvas.addEventListener('touchmove', draw);
  canvas.addEventListener('touchend', stop);

  function clearCanvas() {{
    ctx.fillStyle = "white";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    document.getElementById('status').innerText = '';
  }}

  async function copyImage() {{
    canvas.toBlob(async (blob) => {{
      await navigator.clipboard.write([new ClipboardItem({{ 'image/png': blob }})]);
      document.getElementById('status').innerText = 'Copied! Paste into the box on the right (Ctrl+V).';
    }});
  }}
</script>
"""

col1, col2 = st.columns([1.2, 1])
with col1:
    st.caption("1. Draw your problem below, then click **Copy Drawing**")
    components.html(canvas_html, height=460)

with col2:
    st.caption("2. Click the box below and press **Ctrl+V** (or upload a photo)")
    pasted_or_uploaded = st.file_uploader("Paste or upload problem image", type=["png", "jpg", "jpeg"])
    extra_notes = st.text_input("Optional hint (e.g., 'Solve for x'):")

    if st.button("Solve Problem", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        elif not pasted_or_uploaded:
            st.warning("Please paste (Ctrl+V) or upload your drawing first.")
        else:
            with st.spinner("Solving..."):
                img = Image.open(pasted_or_uploaded).convert("RGB")
                client = genai.Client(api_key=api_key)
                prompt = f"Transcribe this handwritten problem in LaTeX and solve it step-by-step. Hint: {extra_notes}"
                response = client.models.generate_content(model="gemini-2.5-flash", contents=[img, prompt])
                st.markdown(response.text)
