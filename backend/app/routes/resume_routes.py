from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from io import BytesIO
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
import json
from datetime import datetime

from app.database import get_db, SessionLocal
from app.auth import get_current_user
from app.models import ResumeAnalysis
from app.services.resume_parser import extract_text_from_pdf
from app.services.gemini_service import analyze_resume_with_gemini
from app.services.scoring_service import rank_resumes

router = APIRouter(prefix="/resumes", tags=["Resume Analysis"])


# ============================================================
# 🔥 BACKGROUND FUNCTION (OUTSIDE ROUTE)
# ============================================================
def process_resume_analysis(
    analysis_id: int,
    job_description: str,
    files_data: List[dict]
):
    db = SessionLocal()

    try:
        extracted_resumes = []

        for file in files_data:
            text = extract_text_from_pdf(BytesIO(file["content"]))
             # 🔎 DEBUG BLOCK (temporary)
            print("\n===== DEBUG: Extracted Resume Text =====")
            print(text[:500])   # print first 500 chars only
            print("========================================\n")

            result = analyze_resume_with_gemini(text, job_description)

            extracted_resumes.append({
                "file_name": file["filename"],
                **result
            })

        final_results = rank_resumes(extracted_resumes)

        analysis = db.query(ResumeAnalysis).filter(
            ResumeAnalysis.id == analysis_id
        ).first()

        analysis.total_resumes = len(final_results)
        analysis.ranked_results = json.dumps(final_results)
        analysis.status = "completed"

        db.commit()

    except Exception as e:
          
        print("\n🔥 BACKGROUND ERROR OCCURRED 🔥")
        print(str(e))
        print("=================================\n")

        analysis = db.query(ResumeAnalysis).filter(
            ResumeAnalysis.id == analysis_id
        ).first()

        analysis.status = "failed"
        db.commit()

    finally:
        db.close()


# ============================================================
# POST /resumes/analyze
# ============================================================
@router.post("/analyze")
async def analyze_resumes(
    background_tasks: BackgroundTasks,
    job_description: str = Form(...),
    job_role: str = Form(""),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No resumes uploaded")

    # 1️⃣ Create DB record FIRST
    analysis = ResumeAnalysis(
        user_id=current_user.id,
        job_role=job_role,
        job_description=job_description,
        total_resumes=0,
        ranked_results=None,
        status="processing"
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # 2️⃣ Store file content in memory for background task
    files_data = []
    for file in files:
        content = await file.read()
        files_data.append({
            "filename": file.filename,
            "content": content
        })

    # 3️⃣ Run background processing
    background_tasks.add_task(
        process_resume_analysis,
        analysis.id,
        job_description,
        files_data
    )

    return {
        "analysis_id": analysis.id,
        "status": "processing",
        "message": "Resume analysis started in background"
    }


# ============================================================
# GET /resumes/my-analyses
# ============================================================
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
            "status": a.status,
            "created_at": a.created_at
        }
        for a in analyses
    ]


# ============================================================
# GET /resumes/{analysis_id}
# ============================================================
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

    if analysis.status != "completed":
        return {
            "analysis_id": analysis.id,
            "status": analysis.status,
            "message": "Analysis still processing"
        }

    return {
        "analysis_id": analysis.id,
        "job_role": analysis.job_role,
        "total_resumes": analysis.total_resumes,
        "results": json.loads(analysis.ranked_results)
    }


# ============================================================
# DOWNLOAD
# ============================================================
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

    if not analysis or analysis.status != "completed":
        raise HTTPException(status_code=404, detail="Analysis not ready")

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

    job_role_clean = analysis.job_role.strip().replace(" ", "_")
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
