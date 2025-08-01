import google.generativeai as genai

# ✅ Your API key MUST be in double quotes
genai.configure(api_key="AIzaSyDEdhsiBJiQJ8W27d-ChqokwIHQJ4CIS_s")

model = genai.GenerativeModel("gemini-1.5-flash")

prompt = "Hello, can you confirm my Gemini API key is working?"

response = model.generate_content(prompt)
print("✅ Gemini replied:", response.text)
