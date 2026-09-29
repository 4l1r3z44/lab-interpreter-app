import streamlit as st
import base64
import io
from PIL import Image
import pymupdf  # PyMuPDF
from openai import OpenAI

# Initialize OpenAI client from Streamlit secrets
client = OpenAI(
    api_key=st.secrets["AVALAI_API_KEY"],
    base_url="https://api.avalai.ir/v1"
)

st.set_page_config(page_title="Clinical Lab Interpreter", page_icon="🔬", layout="centered")

st.title("🔬 Clinical Lab Interpreter")
st.markdown("Upload lab results (**PDF** or **Image**) to generate a plain-language summary of your biomarkers.")

uploaded_file = st.file_uploader("Upload lab results", type=["pdf", "png", "jpg", "jpeg"])

def get_base64_from_image(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_type = uploaded_file.type
    
    preview_images = []
    base64_payloads = []

    # Handle PDF uploads
    if "pdf" in file_type:
        with st.spinner("Extracting PDF pages..."):
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # 2x zoom preserves legibility of small lab reference tables
                pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                png_bytes = pix.tobytes("png")
                
                base64_payloads.append(get_base64_from_image(png_bytes))
                preview_images.append(Image.open(io.BytesIO(png_bytes)))

    # Handle Image uploads
    else:
        preview_images.append(Image.open(uploaded_file))
        base64_payloads.append(get_base64_from_image(file_bytes))

    # Display page previews
    st.divider()
    st.subheader(f"Document Preview ({len(preview_images)} Page{'s' if len(preview_images) > 1 else ''})")
    
    cols = st.columns(min(len(preview_images), 3))
    for i, img in enumerate(preview_images):
        with cols[i % len(cols)]:
            st.image(img, caption=f"Page {i + 1}", width="stretch")

    # Trigger interpretation
    if st.button("Interpret Results 🚀", type="primary", width="stretch"):
        with st.spinner("Analyzing all pages with clinical NLP..."):
            
            # Construct multimodal user message with all pages
            user_content = [
                {
                    "type": "text", 
                    "text": "Please review all pages of this lab report and provide a clear, patient-friendly summary."
                }
            ]
            
            for b64 in base64_payloads:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                })

            system_prompt = """
            You are an empathetic medical educator helping a patient understand their lab test.
            Your task:
            1. Consolidate results across all pages.
            2. Extract each biomarker, patient result, and standard reference range.
            3. For flagged or abnormal markers, explain what the molecule does in plain English using a simple analogy.
            4. Clarify whether it is elevated or low, but DO NOT provide differential diagnoses.
            5. STRICT GUARDRAIL: Do not suggest medications, treatments, or dosages.
            """

            response = client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=2000,
            )

            st.markdown("### 📋 Plain-Language Breakdown")
            st.markdown(response.choices[0].message.content)
            
            st.warning("**Disclaimer:** This report explains medical vocabulary and reference ranges. It is not a diagnosis. Always discuss these results with your physician.")
