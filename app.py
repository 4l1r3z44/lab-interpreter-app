import streamlit as st
import base64
from PIL import Image

# 1. Page Configuration
st.set_page_config(
    page_title="Lab Interpreter",
    page_icon="🔬",
    layout="centered"
)

# 2. Header and Introduction
st.title("🔬 Clinical Lab Interpreter")
st.markdown("""
Upload your lab results (PDF or Image) to receive a plain-language explanation of your biomarkers. 
""")
st.info("This tool translates medical terminology into everyday language. It does not provide medical advice, diagnoses, or treatment plans.")

# 3. File Uploader
uploaded_file = st.file_uploader(
    "Drag and drop your lab results here", 
    type=["pdf", "png", "jpg", "jpeg"],
    help="We accept images or PDF documents."
)

# 4. Processing and Display
if uploaded_file is not None:
    file_type = uploaded_file.type
    
    st.divider()
    st.subheader("Document Preview")
    
    # Display Image preview
    if "image" in file_type:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Lab Result", use_column_width=True)
        
        # Read file as bytes into memory to send to the API later
        file_bytes = uploaded_file.getvalue() 
        
    # Display PDF preview
    elif "pdf" in file_type:
        file_bytes = uploaded_file.getvalue()
        base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
        
        # Embed PDF directly into the web app using an iframe
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    # 5. The Trigger Button
    if st.button("Interpret Results 🚀", type="primary", use_container_width=True):
        
        with st.spinner("Analyzing document structure and reading biomarkers..."):
            
            # -------------------------------------------------------------
            # API INTEGRATION HOOK
            # 1. Encode file_bytes to base64
            # 2. Pass to an LLM Vision API with your system prompt
            # 3. Retrieve the structured response
            # -------------------------------------------------------------
            
            # Mocking the LLM response for testing the UI
            st.success("Analysis Complete!")
            
            st.markdown("### 📋 Your Lab Summary")
            st.markdown("""
            **Biomarker:** Hemoglobin (Hgb)
            * **Your Value:** 11.2 g/dL
            * **Standard Range:** 13.8 to 17.2 g/dL
            * **Explanation:** Think of hemoglobin as the delivery trucks carrying oxygen to your organs. Your value is slightly decreased, meaning you have fewer 'trucks' on the road than usual.
            """)
            
            # Mandatory ethical guardrail 
            st.warning("""
            **Disclaimer:** This report is to help you understand your lab vocabulary. It is not a diagnosis. Always discuss these results with your physician, who understands your complete clinical picture.
            """)
