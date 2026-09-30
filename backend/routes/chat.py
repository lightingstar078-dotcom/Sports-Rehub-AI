from fastapi import APIRouter
from pydantic import BaseModel, Field

from ml.readiness import guidance

router = APIRouter()

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    athlete: dict | None = None
    assessment: dict | None = None
    online: bool = False

def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _factors(assessment: dict) -> list[str]:
    factors = []
    for key, label in [
        ('movement_quality', 'movement quality'), ('symmetry', 'left-right symmetry'),
        ('rom', 'range of motion'), ('stability', 'stability'),
        ('landing_control', 'landing control'), ('movement_consistency', 'movement consistency'),
        ('psychological_readiness', 'psychological readiness'),
    ]:
        value = _number(assessment.get(key))
        if value is not None and value < 70:
            factors.append(f'{label} ({value:.0f}/100)')
    pain = _number(assessment.get('pain'))
    if pain is not None and pain >= 4:
        factors.append(f'athlete-reported pain ({pain:.0f}/10)')
    return factors

def _reply(message: str, assessment: dict) -> str:
    text = message.lower()
    score, status = _number(assessment.get('readiness_score')), assessment.get('status')
    factors = _factors(assessment)
    factor_text = ', '.join(factors[:3]) if factors else 'no single low input was identified in the recorded assessment'
    if not assessment or score is None:
        return 'Complete an assessment first. I can then explain the recorded movement, pain, psychological readiness, and recovery-trend inputs. This tool is educational support, not medical clearance.'
    if any(term in text for term in ['why', 'score', 'readiness', 'result', 'explain']):
        return f'Your current readiness indicator is {score:.0f}/100 ({status}). The main recorded factors to review are {factor_text}. Pain and psychological readiness are athlete-reported; movement metrics are derived from the submitted video. This is a screening prototype, not medical clearance.'
    if any(term in text for term in ['pain', 'hurt', 'sore']):
        pain = _number(assessment.get('pain'))
        return f'Your recorded pain is {pain:.0f}/10.' if pain is not None else 'No pain score was recorded for the selected assessment.'
    if any(term in text for term in ['exercise', 'next', 'recover', 'improve', 'training']):
        items = guidance(status, score)
        return 'Suggested next steps: ' + ' '.join(items) + ' Stop or seek professional help if symptoms worsen.'
    if any(term in text for term in ['symmetry', 'rom', 'range', 'stability', 'movement']):
        metrics = []
        for key, label in [('movement_quality', 'movement quality'), ('symmetry', 'symmetry'), ('rom', 'range of motion'), ('stability', 'stability')]:
            value = _number(assessment.get(key))
            if value is not None: metrics.append(f'{label}: {value:.0f}/100')
        return 'Recorded movement metrics: ' + (', '.join(metrics) if metrics else 'not available yet.')
    return f'I can explain your {score:.0f}/100 ({status}) indicator, pain, movement metrics, or recovery guidance. The main factors currently flagged are {factor_text}.'

@router.post('')
def chat(request: ChatRequest):
    assessment = request.assessment or {}
    score, status = _number(assessment.get('readiness_score')), assessment.get('status')
    return {
        'reply': _reply(request.message, assessment),
        'mode': 'online' if request.online else 'offline',
        'guidance': guidance(status, score),
        'assistant_type': 'local assessment-aware recovery support',
    }
