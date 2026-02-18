def rank_resumes(resume_results: list):
    """
    Sort resumes by match_score descending
    """

    sorted_results = sorted(
        resume_results,
        key=lambda x: x.get("match_score", 0),
        reverse=True
    )

    return sorted_results
