import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class RegleMatch:
    regle_id: str
    diagnostic: str
    confiance_regle: float
    score_ajoute: float
    explication: str
    symptomes_obligatoires: List[str]
    symptomes_optionnels: List[str]


def charger_base_connaissances(chemin_json: str) -> Dict:
    chemin = Path(chemin_json)
    with chemin.open("r", encoding="utf-8") as f:
        return json.load(f)


def _regle_applicable(regle: Dict, symptomes_presents: Set[str]) -> Tuple[bool, List[str], List[str]]:
    si_tous = set(regle.get("si_tous", []))
    si_un = set(regle.get("si_un", []))

    if si_tous and not si_tous.issubset(symptomes_presents):
        return False, [], []

    matched_tous = sorted(list(si_tous & symptomes_presents))

    matched_un: List[str] = []
    if si_un:
        matched_un = sorted(list(si_un & symptomes_presents))
        if len(matched_un) == 0:
            return False, [], []

    return True, matched_tous, matched_un


def _combiner_scores(score_actuel: float, score_ajoute: float) -> float:
    return 1.0 - (1.0 - score_actuel) * (1.0 - score_ajoute)


def _calculer_score_regle(regle: Dict, matched_un: List[str]) -> Tuple[float, float]:
    confiance = float(regle.get("confiance", 0.5))

    si_un = regle.get("si_un", [])
    bonus = 1.0
    if si_un:
        bonus = max(0.6, len(matched_un) / len(si_un))

    score_ajoute = max(0.0, min(1.0, confiance * bonus))
    return confiance, score_ajoute


def inferer_diagnostics(base: Dict, symptomes_presents: Set[str]) -> Tuple[Dict[str, float], Dict[str, List[RegleMatch]]]:
    regles = base.get("regles", [])
    scores: Dict[str, float] = {}
    traces: Dict[str, List[RegleMatch]] = {}

    for regle in regles:
        ok, matched_tous, matched_un = _regle_applicable(regle, symptomes_presents)
        if not ok:
            continue

        diagnostic = regle["diagnostic"]
        confiance, score_ajoute = _calculer_score_regle(regle, matched_un)

        prev = scores.get(diagnostic, 0.0)
        scores[diagnostic] = _combiner_scores(prev, score_ajoute)

        traces.setdefault(diagnostic, []).append(
            RegleMatch(
                regle_id=regle["id"],
                diagnostic=diagnostic,
                confiance_regle=confiance,
                score_ajoute=score_ajoute,
                explication=regle.get("explication", ""),
                symptomes_obligatoires=matched_tous,
                symptomes_optionnels=matched_un,
            )
        )

    for diag in traces:
        traces[diag].sort(key=lambda m: m.score_ajoute, reverse=True)

    return scores, traces


def _index_regles_par_diagnostic(base: Dict) -> Dict[str, List[Dict]]:
    index: Dict[str, List[Dict]] = {}
    for r in base.get("regles", []):
        diag = r.get("diagnostic")
        if not diag:
            continue
        index.setdefault(diag, []).append(r)
    return index


def _prouver_diagnostic(
    diagnostic: str,
    regles_index: Dict[str, List[Dict]],
    symptomes_presents: Set[str],
) -> Tuple[float, List[RegleMatch]]:
    regles = regles_index.get(diagnostic, [])
    score_total = 0.0
    matches: List[RegleMatch] = []

    for regle in regles:
        ok, matched_tous, matched_un = _regle_applicable(regle, symptomes_presents)
        if not ok:
            continue

        confiance, score_ajoute = _calculer_score_regle(regle, matched_un)
        score_total = _combiner_scores(score_total, score_ajoute)

        matches.append(
            RegleMatch(
                regle_id=regle["id"],
                diagnostic=diagnostic,
                confiance_regle=confiance,
                score_ajoute=score_ajoute,
                explication=regle.get("explication", ""),
                symptomes_obligatoires=matched_tous,
                symptomes_optionnels=matched_un,
            )
        )

    matches.sort(key=lambda m: m.score_ajoute, reverse=True)
    return score_total, matches


def inferer_diagnostics_arriere(
    base: Dict,
    symptomes_presents: Set[str],
    diagnostics_cibles: Optional[List[str]] = None,
) -> Tuple[Dict[str, float], Dict[str, List[RegleMatch]]]:
    regles_index = _index_regles_par_diagnostic(base)

    if diagnostics_cibles is not None:
        diagnostics = diagnostics_cibles
    else:
        diagnostics = list(base.get("diagnostics", []))

    scores: Dict[str, float] = {}
    traces: Dict[str, List[RegleMatch]] = {}

    for diag in diagnostics:
        score, matches = _prouver_diagnostic(diag, regles_index, symptomes_presents)
        if score > 0.0:
            scores[diag] = score
            traces[diag] = matches

    return scores, traces


def top_k(scores: Dict[str, float], k: int = 3) -> List[Tuple[str, float]]:
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]


def filtrer_symptomes_inconnus(base: Dict, symptomes: Set[str]) -> Tuple[Set[str], Set[str]]:
    connus = set(base.get("symptomes", []))
    valides = {s for s in symptomes if s in connus}
    inconnus = symptomes - valides
    return valides, inconnus
