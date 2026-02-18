from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
from io import BytesIO
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
import json
from datetime import datetime


from app.database import get_db
from app.auth import get_current_user
from app.models import ResumeAnalysis
from app.services.resume_parser import extract_text_from_pdf
from app.services.gemini_service import analyze_resume_with_gemini
from app.services.scoring_service import rank_resumes

router = APIRouter(prefix="/resumes", tags=["Resume Analysis"])


# ================================
# POST /resumes/analyze
# ================================
@router.post("/analyze")
async def analyze_resumes(
    job_description: str = Form(...),
    job_role: str = Form(""),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No resumes uploaded")

    extracted_resumes = []

    # 1️⃣ Extract text
    for file in files:
        content = await file.read()
        text = extract_text_from_pdf(BytesIO(content))

        # 2️⃣ Analyze with Gemini
        result = analyze_resume_with_gemini(text, job_description)

        extracted_resumes.append({
            "file_name": file.filename,
            **result
        })

    # 3️⃣ Rank results (your scoring service)
    final_results = rank_resumes(extracted_resumes)

    # 4️⃣ Save entire batch as ONE record
    analysis = ResumeAnalysis(
        user_id=current_user.id,
        job_role=job_role,
        job_description=job_description,
        total_resumes=len(final_results),
        ranked_results=json.dumps(final_results)
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {
        "analysis_id": analysis.id,
        "job_role": job_role,
        "total_resumes": len(final_results),
        "results": final_results
    }


# ================================
# GET /resumes/my-analyses
# ================================
@router.get("/my-analyses")
def get_my_analyses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    analyses = db.query(ResumeAnalysis) \
        .filter(ResumeAnalysis.user_id == current_user.id) \
        .order_by(ResumeAnalysis.created_at.desc()) \
        .limit(10) \
        .all()

    return [
        {
            "analysis_id": a.id,
            "job_role": a.job_role,
            "total_resumes": a.total_resumes,
            "created_at": a.created_at
        }
        for a in analyses
    ]


# ================================
# GET /resumes/{analysis_id}
# ================================
@router.get("/{analysis_id}")
def get_analysis_detail(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    analysis = db.query(ResumeAnalysis) \
        .filter(
            ResumeAnalysis.id == analysis_id,
            ResumeAnalysis.user_id == current_user.id
        ) \
        .first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "analysis_id": analysis.id,
        "job_role": analysis.job_role,
        "total_resumes": analysis.total_resumes,
        "results": json.loads(analysis.ranked_results)
    }


# ================================
# GET /resumes/{analysis_id}/download
# ================================
@router.get("/{analysis_id}/download")
def download_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    analysis = db.query(ResumeAnalysis) \
        .filter(
            ResumeAnalysis.id == analysis_id,
            ResumeAnalysis.user_id == current_user.id
        ) \
        .first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    results = json.loads(analysis.ranked_results)

    wb = Workbook()
    ws = wb.active
    ws.title = "Ranked Resumes"

    ws.append([
        "File Name",
        "Name",
        "Contact",
        "Email",
        "Match Score",
        "Interview Priority"
    ])

    for r in results:
        ws.append([
            r.get("file_name"),
            r.get("name"),
            r.get("contact_number"),
            r.get("email"),
            r.get("match_score"),
            r.get("interview_priority"),
        ])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    # ✅ Clean job role for filename
    job_role_clean = analysis.job_role.strip().replace(" ", "_")

    # ✅ Add date
    today_str = datetime.now().strftime("%Y-%m-%d")

    file_name = f"{job_role_clean}_{today_str}.xlsx"

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
                f"attachment; filename={file_name}"
        },
    )
