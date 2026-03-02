class ResumeAnalysisError(Exception):
    pass


class QuotaExceededError(ResumeAnalysisError):
    pass


class ForbiddenError(ResumeAnalysisError):
    pass


class ResumeParseError(ResumeAnalysisError):
    pass


class UnsupportedFileTypeError(ResumeParseError):
    pass
