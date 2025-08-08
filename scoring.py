
import re
from typing import Dict, Any

GOLD_KEY_PHRASES = [
    "neutral step",
    "full and fair investigation",
    "without prejudice",
    "lawful free expression",
    "free expression",
    "free speech",
    "harassment or discrimination",
    "zero tolerance",
    "consider all relevant evidence",
    "we will not be making further comment",
    "respect for due process",
]

def score_statement(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        return {"score": 0, "notes": ["No statement provided."], "matches": []}

    lower = text.lower()
    matches = [p for p in GOLD_KEY_PHRASES if p in lower]

    clarity = 1 if ("suspend" in lower or "suspension" in lower) and ("investig" in lower) else 0
    balance = 1 if ("free speech" in lower or "free expression" in lower) and ("harassment" in lower or "discrimination" in lower) else 0
    tone = 1 if all(term not in lower for term in ["woke", "witch hunt", "mob", "racist!", "hate speech!"]) else 0
    control = 1 if ("further comment" in lower or "no further comment" in lower) else 0

    base = len(matches) * 5  # up to 50 points for key phrase alignment
    rubric = clarity*15 + balance*15 + tone*10 + control*10  # up to 50
    total = min(100, base + rubric)

    notes = []
    if not clarity: notes.append("Add clear process: precautionary suspension and investigation.")
    if not balance: notes.append("Balance both: free speech/expression AND zero tolerance for harassment/discrimination.")
    if not tone: notes.append("Avoid emotionally loaded terms that could inflame coverage.")
    if not control: notes.append("Include a line controlling information flow (e.g., no further comment during investigation).")
    if matches: notes.append(f"Good alignment with best practice phrases: {', '.join(matches[:5])}" + ("..." if len(matches) > 5 else ""))

    return {"score": total, "notes": notes, "matches": matches}

def score_decisions(decisions: Dict[str, str]) -> Dict[str, Any]:
    # Very simple heuristic scoring of key decision points
    pts = 0
    notes = []

    # Early response vs delay
    early = decisions.get("respond_now", "").lower()
    if "respond" in early:
        pts += 15
        notes.append("Responded early with a holding statement to shape the frame.")
    else:
        notes.append("Delayed response; risked losing the narrative.")

    # BBC interview
    bbc = decisions.get("bbc_request", "").lower()
    if "written" in bbc or "deputy" in bbc:
        pts += 10
        notes.append("Chose controlled format for BBC request (written or deputy).")
    else:
        notes.append("Accepted live principal interview; higher risk unless extremely well-prepped.")

    # Charity story timing
    charity = decisions.get("charity_story", "").lower()
    if "hold" in charity:
        pts += 10
        notes.append("Held the unrelated positive story to avoid appearing evasive.")
    else:
        notes.append("Pushed positive story during crisis; could be perceived as deflection.")

    return {"score": pts, "notes": notes}
