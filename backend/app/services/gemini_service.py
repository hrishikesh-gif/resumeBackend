import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv("key.env")

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

MODEL_NAME = "gemini-2.5-flash"


def analyze_resume_with_gemini(resume_text: str, job_description: str):
    """
    Minimal AI response to reduce token usage.
    """

    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""
    Extract candidate information from the resume and compare with job description.

    Return ONLY valid JSON in this exact format:

    {{
      "name": "",
      "contact_number": "",
      "email": "",
      "match_score": 0,
      "interview_priority": "High" | "Medium" | "Low"
    }}

    Job Description:
    {job_description}

    Resume:
    {resume_text[:4000]}
    """

    response = model.generate_content(prompt)

    try:
        clean_text = response.text.strip("```json").strip("```")
        return json.loads(clean_text)
    except Exception:
        return {
            "name": "Not Found",
            "contact_number": "Not Found",
            "email": "Not Found",
            "match_score": 0,
            "interview_priority": "Low"
        }
