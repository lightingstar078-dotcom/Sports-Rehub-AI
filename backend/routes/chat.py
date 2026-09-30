from fastapi import APIRouter
from pydantic import BaseModel
from ml.readiness import guidance

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    athlete: dict | None = None
    assessment: dict | None = None
    online: bool = False

@router.post("")
def chat(req: ChatRequest):
    msg = req.message.lower()
    a = req.assessment or {}
    score = a.get("readiness_score")
    status = a.get("status")
    if "score" in msg or "readiness" in msg:
        if score is None:
            reply = "A readiness score is not available until a real trained ML model is installed and evaluated."
        else:
            reply = f"The current readiness indicator is {score}/100 ({status}). The movement and athlete-reported factors are shown in your assessment dashboard."
    elif "pain" in msg:
        reply = f"The athlete-reported pain score for the selected assessment is {a.get('pain','not recorded')}/10. This is athlete-reported information, not a diagnosis."
    elif "why" in msg:
        reply = "Review Movement Quality, Symmetry, ROM, Stability, Pain, Psychological Readiness and the Recovery Trend. These are the main inputs used by the system."
    else:
        reply = "I can explain your readiness score, movement metrics, pain, psychological readiness, recovery trend, functional tests, or the project technology."
    return {"reply": reply, "mode": "online" if req.online else "offline", "guidance": guidance(status, score)}
