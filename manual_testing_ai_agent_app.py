import streamlit as st
import google.generativeai as genai
import pandas as pd
from openpyxl import Workbook
from io import BytesIO
import google.api_core.exceptions  # Needed for catching quota errors

# Load API key from Streamlit secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Streamlit page setup
st.set_page_config(page_title="T.A.R.G.E.T", layout="wide")

# Welcome message for first-time users
with st.container():
    st.title("🎯 T.A.R.G.E.T")
    st.markdown("""
    👋 **Welcome!** This AI-powered tool helps you generate simple, checkbox-style manual test cases for any module or feature. 

    ✅ Select the type of test cases you want (Functional, Regression, Security)  
    ✍️ Enter the feature/module name  
    🔢 Choose how many test cases to generate  
    ☑️ Mark Pass/Fail for each test case  
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

# Model selector (only gemini-1.5-flash)
model_type = st.selectbox("🤖 Gemini Model", ["gemini-1.5-flash"], index=0, help="Choose Gemini AI model to use.")

# Module input
module_name = st.text_input("🔍 Enter Module or Feature to Test:", help="Type the name of the module you want to generate test cases for.")

# Number of test cases
num_cases = st.slider("🧮 Number of Test Cases", min_value=5, max_value=20, value=10, help="Use the slider to pick how many test cases to generate.")

# Reset button
if st.button("🔄 Reset Inputs"):
    st.experimental_rerun()

def parse_markdown_table(md_text):
    """
    Parses a markdown table string and returns a pandas DataFrame.
    """
    lines = [line for line in md_text.splitlines() if line.strip()]
    table_lines = [line for line in lines if "|" in line]
    if not table_lines:
        return None
    # Remove separator lines (e.g., |---|---|)
    table_lines = [line for line in table_lines if not set(line.replace('|', '').strip()) <= set('-: ')]
    if len(table_lines) < 2:
        return None
    header = [col.strip() for col in table_lines[0].split("|")[1:-1]]
    data = []
    for line in table_lines[1:]:
        row = [col.strip() for col in line.split("|")[1:-1]]
        if len(row) == len(header):
            data.append(row)
    if not data:
        return None
    return pd.DataFrame(data, columns=header)

if module_name:
    # Compose prompt based on selection
    if prompt_type == "Functional Test Cases":
        prompt = (
            f"Generate {num_cases} simple functional manual test cases for the '{module_name}' module. "
            "Each test case should be very simple and in a markdown table with columns: Test Case ID, Description, Steps, Expected Result. "
            "Do not include Preconditions. Keep the test cases short and clear."
        )
    elif prompt_type == "Regression Scenarios":
        prompt = (
            f"List {num_cases} simple regression test scenarios for the '{module_name}' module in markdown table format: "
            "Test Case ID, Area Affected, Description, Steps, Expected Outcome. "
            "Keep the test cases short and clear."
        )
    else:
        prompt = (
            f"Create {num_cases} simple security test cases for the '{module_name}' feature in markdown table format: "
            "Test ID, Risk Type, Test Description, Expected Result. "
            "Keep the test cases short and clear."
        )

    try:
        with st.spinner("🔄 Generating test cases..."):
            model = genai.GenerativeModel(model_type)
            response = model.generate_content(prompt)
            output = response.text.strip()

        st.success("✅ Test cases generated!")

        # Try to parse markdown table
        df = parse_markdown_table(output)
        if df is not None and not df.empty:
            # Auto-tick Pass/Fail based on Expected Result
            def auto_pass_fail(row):
                expected = ""
                # Try to find the expected result column
                for col in row.index:
                    if "expected" in col.lower():
                        expected = str(row[col]).lower()
                        break
                # Define pass/fail keywords
                pass_keywords = [
                    "login successful", "success", "logged in", "access granted",
                    "should allow", "should be able", "user is logged in", "user should be logged in"
                ]
                fail_keywords = [
                    "fail", "error", "invalid", "required", "not allowed", "missing",
                    "should not allow", "should not be able", "login fails", "login should fail",
                    "user is not logged in", "user should not be logged in"
                ]
                if any(k in expected for k in pass_keywords):
                    return True
                if any(k in expected for k in fail_keywords):
                    return False
                return False  # Default unchecked

            df["Pass/Fail"] = df.apply(auto_pass_fail, axis=1)

            # Use Streamlit's editable dataframe for checkboxes
            edited_df = st.data_editor(
                df,
                column_config={
                    "Pass/Fail": st.column_config.CheckboxColumn(
                        "Pass/Fail", help="Mark as Pass or Fail"
                    )
                },
                disabled=df.columns[:-1],  # Only allow editing Pass/Fail
                hide_index=True,
                key="testcase_editor"
            )
        else:
            st.markdown(output)
            st.warning("⚠️ Could not format table, displaying raw text.")

        # Excel export
        if st.button("📥 Export to Excel"):
            export_df = edited_df if 'edited_df' in locals() else df
            if export_df is not None and not export_df.empty:
                wb = Workbook()
                ws = wb.active
                ws.title = f"{module_name} Test Cases"

                # Write header
                ws.append(list(export_df.columns))

                # Write data rows
                for r in export_df.itertuples(index=False):
                    ws.append(list(r))

                excel_data = BytesIO()
                wb.save(excel_data)
                excel_data.seek(0)

                st.download_button(
                    label="⬇️ Download Excel File",
                    data=excel_data,
                    file_name=f"{module_name}_{prompt_type.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("❌ No valid table data to export. Please check the generated test cases above.")

    except google.api_core.exceptions.ResourceExhausted as e:
        st.error("🚫 You’ve reached your Gemini API quota for today. Please try again after 24 hours or upgrade your plan.")
        st.caption("You can check usage limits at: https://ai.google.dev/gemini-api/docs/rate-limits")
    except Exception as e:
        st.error(f"❌ An error occurred while generating test cases: {str(e)}")
        
