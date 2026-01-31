from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from moteur_inference import (
    charger_base_connaissances,
    inferer_diagnostics,
    inferer_diagnostics_arriere,
    top_k,
    filtrer_symptomes_inconnus,
)

BASE_PATH = ROOT / "src" / "base_connaissances.json"

app = FastAPI(title="API Système Expert Médical")


class SymptomesInput(BaseModel):
    symptomes: List[str]
    mode: Literal["avant", "arriere"] = "avant"


class DiagnosticOutput(BaseModel):
    diagnostic: str
    score: float
    explications: List[str]


@app.post("/diagnostic", response_model=List[DiagnosticOutput])
def diagnostic(data: SymptomesInput):
    base = charger_base_connaissances(str(BASE_PATH))

    symptomes_valides, inconnus = filtrer_symptomes_inconnus(base, set(data.symptomes))
    if not symptomes_valides:
        raise HTTPException(status_code=400, detail="Aucun symptôme valide.")

    if data.mode == "avant":
        scores, traces = inferer_diagnostics(base, symptomes_valides)
    else:
        scores, traces = inferer_diagnostics_arriere(base, symptomes_valides)

    resultats = []
    for diag, score in top_k(scores, k=3):
        explications = []
        if diag in traces:
            explications = [m.explication for m in traces[diag]]

        resultats.append(
            DiagnosticOutput(
                diagnostic=diag,
                score=round(score, 3),
                explications=explications,
            )
        )

    return resultats
