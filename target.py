import streamlit as st
import google.generativeai as genai
import PyPDF2
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import re
import json

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="Manual Testing Agent", page_icon="🧪", layout="centered")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.markdown("### Manual Testing Agent")
    st.info("Upload a PDF requirement document and generate comprehensive test cases using Gemini AI.", icon="📄")
    st.markdown("---")
    st.write("Created by Naveen kumar")

st.title("🧪 Manual Testing Agent (Gemini AI)")
st.markdown("""
<style>
    .stApp {background-color: #f8f9fa;}
    .stButton>button {background-color: #4F8BF9; color: white;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
#### 📄 **Step 1:** Upload your requirement PDF  
#### 🤖 **Step 2:** Click to generate comprehensive test cases  
#### 📥 **Step 3:** Download results as Excel or PDF
""")

uploaded_file = st.file_uploader("**Upload PDF Requirement Document**", type=["pdf"])

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def generate_test_cases(requirements_text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are a professional QA Test Engineer. Based on the following requirement document,
    generate as many comprehensive test cases as needed (module-wise) in JSON format with these fields:

    - ID
    - Module (Admin, HR, API, Security, Performance, Database, etc.)
    - Title
    - Description
    - Precondition
    - Test Steps
    - Expected Result
    - Priority (High, Medium, Low)
    - Test Type (Functional, Regression, Security, Negative, Performance)

    Document:
    {requirements_text}

    Return only JSON array. No explanations.
    """
    response = model.generate_content(prompt)
    text = response.text.strip()

    # Remove code block markers and extract JSON
    text = re.sub(r"^```json|^```|```$", "", text, flags=re.MULTILINE).strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        json_str = match.group(0)
    else:
        json_str = text

    try:
        test_cases = json.loads(json_str)
    except Exception:
        test_cases = [{
            "ID": "ERR-1",
            "Module": "Parsing",
            "Title": "Error parsing response",
            "Description": text,
            "Precondition": "N/A",
            "Test Steps": "N/A",
            "Expected Result": "N/A",
            "Priority": "N/A",
            "Test Type": "N/A"
        }]
    return test_cases

def export_to_excel(test_cases):
    df = pd.DataFrame(test_cases)
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name="TestCases")
    output.seek(0)
    return output

def export_to_pdf(test_cases):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y, "Generated Test Cases")
    y -= 30

    c.setFont("Helvetica", 10)
    for tc in test_cases:
        c.drawString(30, y, f"ID: {tc.get('ID', '')}, Module: {tc.get('Module', '')}, Priority: {tc.get('Priority', '')}")
        y -= 15
        c.drawString(30, y, f"Title: {tc.get('Title', '')}")
        y -= 15
        c.drawString(30, y, f"Description: {tc.get('Description', '')}")
        y -= 15
        c.drawString(30, y, f"Precondition: {tc.get('Precondition', '')}")
        y -= 15
        c.drawString(30, y, f"Test Steps: {tc.get('Test Steps', '')}")
        y -= 15
        c.drawString(30, y, f"Expected Result: {tc.get('Expected Result', '')}")
        y -= 30

        if y < 50:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica", 10)

    c.save()
    buffer.seek(0)
    return buffer

if uploaded_file:
    with st.spinner("🔍 Extracting text from PDF..."):
        extracted_text = ""
        try:
            extracted_text = extract_text_from_pdf(uploaded_file)
        except Exception as e:
            st.error(f"Error reading PDF: {e}")

    if extracted_text:
        st.success("✅ PDF processed successfully!")
        if st.button("🚀 Generate Comprehensive Test Cases"):
            with st.spinner("🤖 Generating test cases with Gemini..."):
                test_cases = generate_test_cases(extracted_text)

                st.subheader("🧪 Generated Test Cases")
                df = pd.DataFrame(test_cases)
                st.dataframe(df, use_container_width=True)

                excel_file = export_to_excel(test_cases)
                pdf_file = export_to_pdf(test_cases)

                st.download_button(
                    label="⬇️ Download Test Cases as Excel",
                    data=excel_file,
                    file_name="test_cases.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                st.download_button(
                    label="⬇️ Download Test Cases as PDF",
                    data=pdf_file,
                    file_name="test_cases.pdf",
                    mime="application/pdf",
                )
    else:
        st.error("❌ No text could be extracted from the PDF. Please check your file.")

else:
    st.info("👆 Please upload a PDF file to begin.", icon="📄")
