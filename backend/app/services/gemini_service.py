from google import genai
from google.genai import types
import json

from app.config import GOOGLE_API_KEY
from .exceptions import ForbiddenError, QuotaExceededError, ResumeAnalysisError

client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

MODEL_NAME = "gemini-2.5-flash"


def analyze_resume_with_gemini(resume_text: str, job_description: str):
    if client is None:
        raise ResumeAnalysisError("GOOGLE_API_KEY is not configured")

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

    try:
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
    except Exception as e:
        msg = str(e).lower()
        if "quota" in msg or "rate limit" in msg or "429" in msg:
            raise QuotaExceededError("Gemini quota exceeded") from e
        if "permission" in msg or "forbidden" in msg or "403" in msg:
            raise ForbiddenError("Gemini access forbidden") from e
        raise ResumeAnalysisError("Gemini analysis failed") from e

    try:
        return json.loads(response.text)
    except Exception as e:
        raise ResumeAnalysisError("Gemini returned invalid JSON response") from e
