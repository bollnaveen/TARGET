import streamlit as st
import google.generativeai as genai
import pandas as pd
from openpyxl import Workbook
from io import BytesIO
import google.api_core.exceptions  # Needed for catching quota errors

# Load API key from Streamlit secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Streamlit page setup
st.set_page_config(page_title="Manual Testing AI Agent", layout="wide")

# Welcome message for first-time users
with st.container():
    st.title("🧪 Manual Testing AI Agent")
    st.markdown("""
    👋 **Welcome!** This AI-powered tool helps you generate structured manual test cases for any module or feature. 

    ✅ Select the type of test cases you want (Functional, Regression, Security)  
    ✍️ Enter the feature/module name  
    🔢 Choose how many test cases to generate  
    📊 View them as a table or 📥 download as Excel
    """)

# Prompt type selection with descriptions
st.markdown("### 📌 Choose What to Generate")
with st.expander("ℹ️ Test Case Types Explained"):
    st.markdown("""
    - **Functional Test Cases**: Basic tests that check if the module works as expected (e.g., Login should succeed with correct credentials).
    - **Regression Scenarios**: Tests that ensure new changes don’t break existing features.
    - **Security Test Cases**: Tests that check for potential vulnerabilities or unauthorized access attempts.
    """)

prompt_type = st.selectbox("Select test case type:", [
    "Functional Test Cases",
    "Regression Scenarios",
    "Security Test Cases"], help="Select the type of manual testing you want to generate.")

# Model selector
model_type = st.selectbox("🤖 Gemini Model", ["gemini-1.5-flash", "gemini-pro"], index=0, help="Choose Gemini AI model to use.")

# Module input
module_name = st.text_input("🔍 Enter Module or Feature to Test:", help="Type the name of the module you want to generate test cases for.")

# Number of test cases
num_cases = st.slider("🧮 Number of Test Cases", min_value=5, max_value=20, value=10, help="Use the slider to pick how many test cases to generate.")

# Reset button
if st.button("🔄 Reset Inputs"):
    st.experimental_rerun()

if module_name:
    # Compose prompt based on selection
    if prompt_type == "Functional Test Cases":
        prompt = f"Generate {num_cases} functional manual test cases for the '{module_name}' module. Format as markdown table: Test Case ID, Description, Preconditions, Steps, Expected Result."
    elif prompt_type == "Regression Scenarios":
        prompt = f"List {num_cases} regression test scenarios for the '{module_name}' module in markdown table format: Test Case ID, Area Affected, Description, Steps, Expected Outcome."
    else:
        prompt = f"Create {num_cases} security test cases for the '{module_name}' feature in markdown table format: Test ID, Risk Type, Test Description, Expected Result."

    try:
        with st.spinner("🔄 Generating test cases..."):
            model = genai.GenerativeModel(model_type)
            response = model.generate_content(prompt)
            output = response.text.strip()

        st.success("✅ Test cases generated!")

        # Display as table
        try:
            rows = [line.split('|')[1:-1] for line in output.splitlines() if '|' in line and not line.startswith('|---')]
            df = pd.DataFrame(rows[1:], columns=[col.strip() for col in rows[0]])
            st.dataframe(df)
        except Exception as e:
            st.markdown(output)
            st.warning("⚠️ Could not format table, displaying raw text.")

        # Excel export
        if st.button("📥 Export to Excel"):
            wb = Workbook()
            ws = wb.active
            ws.title = f"{module_name} Test Cases"

            for r in df.itertuples(index=False):
                ws.append(r)

            excel_data = BytesIO()
            wb.save(excel_data)
            excel_data.seek(0)

            st.download_button(
                label="⬇️ Download Excel File",
                data=excel_data,
                file_name=f"{module_name}_{prompt_type.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except google.api_core.exceptions.ResourceExhausted as e:
        st.error("🚫 You’ve reached your Gemini API quota for today. Please try again after 24 hours or upgrade your plan.")
        st.caption("You can check usage limits at: https://ai.google.dev/gemini-api/docs/rate-limits")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
