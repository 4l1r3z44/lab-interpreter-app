import streamlit as st
import base64
import io
from PIL import Image
import pymupdf  # PyMuPDF
from openai import OpenAI

# 1. Initialize OpenAI client
client = OpenAI(
    api_key=st.secrets["AVALAI_API_KEY"],
    base_url="https://api.avalai.ir/v1"
)

st.set_page_config(page_title="Clinical Lab Interpreter", page_icon="🔬", layout="centered")

# 2. Inject Persian Typography and Spacing CSS
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');

/* Main container for the Persian report */
.persian-report-container {
    direction: rtl;
    text-align: right;
    font-family: 'Vazirmatn', Tahoma, sans-serif;
    font-size: 1.05rem;
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 28px 32px;
    margin-top: 15px;
    margin-bottom: 25px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

/* Ensure airy line height and breathable paragraph margins */
.persian-report-container p {
    line-height: 2.3 !important;
    margin-bottom: 1.6rem !important;
    color: #1e293b;
}

/* Highlighted biomarkers/bold text */
.persian-report-container strong {
    color: #0f172a;
    font-weight: 700;
}

/* List items spacing */
.persian-report-container li {
    line-height: 2.2 !important;
    margin-bottom: 0.75rem !important;
}

/* RTL warning styling */
.persian-warning {
    direction: rtl;
    text-align: right;
    font-family: 'Vazirmatn', Tahoma, sans-serif;
    line-height: 1.9;
    font-size: 0.92rem;
}
</style>
""", unsafe_allow_html=True)

st.title("🔬 Clinical Lab Interpreter")
st.markdown("Upload lab results (**PDF** or **Image**) to generate a plain-language summary of your biomarkers.")

uploaded_file = st.file_uploader("Upload lab results", type=["pdf", "png", "jpg", "jpeg"])

def get_base64_from_image(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")

def load_prompt(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

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
            st.image(img, caption=f"Page {i + 1}", width='content')

    # Trigger interpretation
    if st.button("Interpret Results 🚀", type="primary", width='content'):
        with st.spinner("Analyzing all pages with clinical NLP..."):
            
            user_content = [
                {
                    "type": "text", 
                    "text": "Please review all pages of this lab report and provide a clear, patient-friendly summary in fluent Persian according to your system prompt."
                }
            ]
            
            for b64 in base64_payloads:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                })

            system_prompt = load_prompt("prompt.md")

            response = client.chat.completions.create(
                model="grok-4.5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=5000,
            )

            raw_ai_text = response.choices[0].message.content

            st.markdown("<h3 style='direction: rtl; text-align: right; font-family: Vazirmatn;'>📋 تحلیل و بررسی آزمایش شما</h3>", unsafe_allow_html=True)
            
            # Render Markdown inside RTL container
            # Notice the blank lines before and after raw_ai_text:
            # this ensures the Markdown parser parses bolding and bullet points properly.
            st.markdown(
                f"""
<div class="persian-report-container">

{raw_ai_text}

</div>
""",
                unsafe_allow_html=True
            )
            
            # Persian Disclaimer
            st.warning(
                "**سلب مسئولیت پزشکی:** این گزارش صرفاً جهت آشنایی شما با مفاهیم و اصطلاحات برگه آزمایش تهیه شده و جایگزین تشخیص پزشک نیست. همیشه نتایج نهایی را با پزشک معالج خود درمیان بگذارید.",
                icon="⚠️"
            )