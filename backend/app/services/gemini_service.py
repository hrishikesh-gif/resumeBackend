from google import genai
from google.genai import types
import os
import json
from dotenv import load_dotenv

load_dotenv("key.env")

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL_NAME = "gemini-2.5-flash"


def analyze_resume_with_gemini(resume_text: str, job_description: str):

    prompt = f"""
    Extract candidate information from the resume and compare it with the job description.

    Return:
    - name
    - contact_number
    - email
    - match_score (0-100 based on skill match)
    - interview_priority (High, Medium, Low based on match_score)
    - matched_skills (ONLY skills from resume that match the job description)

    Job Description:
    {job_description}

    Resume:
    {resume_text[:4000]}
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "contact_number": {"type": "string"},
                    "email": {"type": "string"},
                    "match_score": {"type": "number"},
                    "interview_priority": {
                        "type": "string",
                        "enum": ["High", "Medium", "Low"]
                    },
                    "matched_skills": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": [
                    "name",
                    "contact_number",
                    "email",
                    "match_score",
                    "interview_priority",
                    "matched_skills"
                ]
            }
        )
    )

    return json.loads(response.text)