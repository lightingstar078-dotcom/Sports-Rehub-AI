
def guidance(status: str | None, score: float | None):
    if status == "GREEN":
        return ["Continue prescribed recovery exercises.", "Maintain adequate rest and monitor pain.", "Use the current result for further Return-to-Play evaluation."]
    if status == "YELLOW":
        return ["Continue monitoring recovery indicators.", "Reduce progression if pain increases.", "Consider professional review if symptoms persist or worsen."]
    if status == "RED":
        return ["Professional physiotherapist/doctor assessment is recommended before progressing activity."]
    return ["Train and install a real readiness model before using ML classification.", "The prototype can still display video-derived movement features and athlete-reported data."]
