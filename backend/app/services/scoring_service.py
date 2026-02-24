def rank_resumes(resume_results: list):
    """
    Sort resumes by match_score descending
    and assign interview_priority based on score
    """

    # 1️⃣ Sort by numeric score
    sorted_results = sorted(
        resume_results,
        key=lambda x: float(x.get("match_score", 0)),
        reverse=True
    )

    # 2️⃣ Assign priority based on score (overwrite AI value)
    for r in sorted_results:
        score = float(r.get("match_score", 0))

        if score >= 75:
            r["interview_priority"] = "High"
        elif score >= 60:
            r["interview_priority"] = "Medium"
        else:
            r["interview_priority"] = "Low"

    return sorted_results