import base64
import io
import os
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from google import genai
from google.genai.errors import ClientError

st.set_page_config(page_title="AI Drawing Calculator", page_icon="🧮", layout="wide")
st.title("🧮 AI Drawing Calculator")

# Load API key from Streamlit Secrets if available, otherwise ask in sidebar
default_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
with st.sidebar:
    api_key = st.text_input("Gemini API Key", value=default_key, type="password", help="Get a free key from Google AI Studio").strip()
    model_choice = st.selectbox("AI Model", ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-2.5-flash-lite"])
    pen_size = st.slider("Pen Thickness", 2, 12, 4)

col1, col2 = st.columns([1.2, 1])

with col1:
    st.caption("1. Draw your problem below, then click **Send Drawing to AI ➔**")
    canvas_html = f"""
    <div style="font-family: sans-serif;">
      <canvas id="board" width="580" height="380" style="border: 2px solid #555; border-radius: 8px; background: white; cursor: crosshair; touch-action: none;"></canvas>
      <div style="margin-top: 10px; display: flex; gap: 10px; align-items: center;">
        <button onclick="clearCanvas()" style="padding: 8px 16px; border-radius: 6px; border: 1px solid #ccc; cursor: pointer; font-weight: 600;">Clear Board</button>
        <button onclick="sendDrawing()" style="padding: 8px 18px; border-radius: 6px; border: none; background: #ff4b4b; color: white; cursor: pointer; font-weight: 600;">Send Drawing to AI ➔</button>
        <span id="status" style="font-size: 13px; color: #4caf50; font-weight: 600;"></span>
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
        const clientX = e.touches ? e.touches.clientX : e.clientX;
        const clientY = e.touches ? e.touches.clientY : e.clientY;
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

      function sendDrawing() {{
        const dataUrl = canvas.toDataURL('image/png');
        const parentDoc = window.parent.document;
        const inputs = parentDoc.querySelectorAll('input[type="text"]');
        for (let inp of inputs) {{
          if (inp.getAttribute('aria-label') === 'hidden_canvas_data') {{
            inp.focus();
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeSetter.call(inp, dataUrl);
            inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
            inp.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }}));
            inp.blur();
            document.getElementById('status').innerText = 'Ready! Click "Solve Problem" ➔';
            break;
          }}
        }}
      }}
    </script>
    """
    components.html(canvas_html, height=450)

with col2:
    st.caption("2. Add an optional hint and click **Solve Problem**")
    extra_notes = st.text_input("Optional hint (e.g., 'Solve for x'):")
    canvas_data = st.text_input("hidden_canvas_data", label_visibility="collapsed", placeholder="Drawing data auto-fills here...")

    if st.button("Solve Problem", type="primary", use_container_width=True):
        if not api_key:
            st.error("Open the sidebar (top-left > arrow) and enter your Gemini API Key.")
        elif not canvas_data.startswith("data:image/png;base64,"):
            st.warning("Click 'Send Drawing to AI ➔' under the board first.")
        else:
            with st.spinner("Reading handwriting and solving..."):
                try:
                    b64_str = canvas_data.split(",")
                    img = Image.open(io.BytesIO(base64.b64decode(b64_str))).convert("RGB")
                    client = genai.Client(api_key=api_key)
                    prompt = f"Transcribe this handwritten problem in LaTeX and solve it step-by-step. Hint: {extra_notes}"
                    response = client.models.generate_content(model=model_choice, contents=[img, prompt])
                    st.markdown(response.text)
                except ClientError as e:
                    st.error(f"Gemini API Error ({e.code}): {e.message}")
