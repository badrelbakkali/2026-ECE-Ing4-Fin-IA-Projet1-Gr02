from moteur_inference import (
    charger_base_connaissances,
    inferer_diagnostics,
    top_k,
    filtrer_symptomes_inconnus,
)

BASE = "groupe-02-systeme-expert-medical/src/base_connaissances.json"

NOMS_DIAGNOSTICS = {
    "rhume": "Rhume",
    "grippe": "Grippe",
    "angine": "Angine",
    "gastro_enterite": "Gastro-entérite",
    "infection_urinaire": "Infection urinaire",
    "migraine": "Migraine",
}

# Phase A: triage rapide (6 questions max)
QUESTIONS_TRIAGE = [
    ("fievre", "Avez-vous de la fièvre ?"),
    ("toux", "Avez-vous de la toux ?"),
    ("mal_de_gorge", "Avez-vous mal à la gorge ?"),
    ("diarrhee", "Avez-vous de la diarrhée ?"),
    ("vomissements", "Avez-vous vomi ?"),
    ("brulures_urinaires", "Ressentez-vous des brûlures en urinant ?"),
]

# Phase B: questions ciblées par diagnostic (on ne pose que celles utiles)
QUESTIONS_PAR_DIAGNOSTIC = {
    "rhume": [
        ("nez_qui_coule", "Avez-vous le nez qui coule ?"),
        ("nez_bouche", "Avez-vous le nez bouché ?"),
        ("eternuements", "Avez-vous des éternuements ?"),
        ("fatigue", "Ressentez-vous une grande fatigue ?"),
    ],
    "grippe": [
        ("fatigue", "Ressentez-vous une grande fatigue ?"),
        ("courbatures", "Avez-vous des courbatures ?"),
        ("douleurs_musculaires", "Avez-vous des douleurs musculaires ?"),
        ("frissons", "Avez-vous des frissons ?"),
        ("toux_seche", "Votre toux est-elle plutôt sèche ?"),
        ("maux_de_tete", "Avez-vous mal à la tête ?"),
    ],
    "angine": [
        ("douleur_deglutition", "Avez-vous mal en avalant ?"),
        ("ganglions_gonfles", "Avez-vous des ganglions gonflés ?"),
        ("voix_rauque", "Avez-vous la voix enrouée ?"),
        ("fievre", "Avez-vous de la fièvre ?"),
    ],
    "gastro_enterite": [
        ("douleurs_abdominales", "Avez-vous des douleurs abdominales ?"),
        ("nausees", "Avez-vous des nausées ?"),
        ("perte_appetit", "Avez-vous une perte d'appétit ?"),
        ("fievre", "Avez-vous de la fièvre ?"),
    ],
    "infection_urinaire": [
        ("envies_frequentes_uriner", "Avez-vous des envies fréquentes d'uriner ?"),
        ("urines_troubles", "Avez-vous remarqué des urines troubles ?"),
        ("douleur_bas_ventre", "Avez-vous une douleur dans le bas du ventre ?"),
        ("fievre", "Avez-vous de la fièvre ?"),
    ],
    "migraine": [
        ("maux_de_tete", "Avez-vous mal à la tête ?"),
        ("douleur_un_cote_tete", "La douleur est-elle surtout d'un côté de la tête ?"),
        ("sensibilite_lumiere", "Êtes-vous sensible à la lumière ?"),
        ("nausees", "Avez-vous des nausées ?"),
        ("aggravation_effort", "La douleur s'aggrave-t-elle à l'effort ?"),
        ("vision_floue", "Avez-vous une vision floue ?"),
        ("vertiges", "Avez-vous des vertiges ?"),
    ],
}


def lire_oui_non(question: str) -> bool:
    while True:
        r = input(f"{question} (o/n) : ").strip().lower()
        if r in {"o", "oui", "y", "yes"}:
            return True
        if r in {"n", "non", "no"}:
            return False
        print("Réponse invalide. Tapez 'o' ou 'n'.")


def determiner_candidats(symptomes: set[str]) -> list[str]:
    candidats = set()

    # ORL
    if "toux" in symptomes or "mal_de_gorge" in symptomes:
        candidats.update({"rhume", "angine", "grippe"})
    if "fievre" in symptomes and ("toux" in symptomes or "mal_de_gorge" in symptomes):
        candidats.update({"grippe", "angine"})

    # Gastro
    if "diarrhee" in symptomes or "vomissements" in symptomes:
        candidats.add("gastro_enterite")

    # Urinaire
    if "brulures_urinaires" in symptomes:
        candidats.add("infection_urinaire")

    # Migraine (si maux de tête, on explore)
    if "maux_de_tete" in symptomes:
        candidats.add("migraine")

    # Si rien n'a match, on garde tout (fallback)
    if not candidats:
        candidats.update(
            {"rhume", "grippe", "angine", "gastro_enterite", "infection_urinaire", "migraine"}
        )

    return sorted(list(candidats))


def poser_questions(symptomes: set[str], questions: list[tuple[str, str]]) -> None:
    for code, question in questions:
        if code in symptomes:
            continue
        if lire_oui_non(question):
            symptomes.add(code)


def afficher_resultats(base: dict, symptomes: set[str]) -> None:
    scores, traces = inferer_diagnostics(base, symptomes)
    top = top_k(scores, k=3)

    print("\n--- Résultats ---")
    if not top:
        print("Aucune règle ne correspond avec les symptômes saisis.")
        return

    for diag, score in top:
        nom = NOMS_DIAGNOSTICS.get(diag, diag)
        print(f"\nDiagnostic possible : {nom} (score={score:.3f})")
        if diag in traces:
            print("Raisonnement (règles déclenchées) :")
            for m in traces[diag]:
                print(f"- {m.regle_id} | +{m.score_ajoute:.3f} | {m.explication}")


def main():
    base = charger_base_connaissances(BASE)

    print("=== Système expert médical (prototype pédagogique) ===")
    print("Ce programme ne remplace pas un avis médical.\n")

    symptomes: set[str] = set()

    # Phase A: triage
    print("Phase 1/2 : questions rapides")
    poser_questions(symptomes, QUESTIONS_TRIAGE)

    # Définir les candidats
    candidats = determiner_candidats(symptomes)

    # Phase B: questions ciblées
    print("\nPhase 2/2 : questions ciblées")
    deja_posees = set(code for code, _ in QUESTIONS_TRIAGE)

    for diag in candidats:
        questions = QUESTIONS_PAR_DIAGNOSTIC.get(diag, [])
        a_poser = [(c, q) for (c, q) in questions if c not in deja_posees]
        poser_questions(symptomes, a_poser)
        deja_posees.update([c for (c, _) in a_poser])

    symptomes_valides, inconnus = filtrer_symptomes_inconnus(base, symptomes)
    if inconnus:
        print("\nSymptômes inconnus ignorés:", ", ".join(sorted(list(inconnus))))

    afficher_resultats(base, symptomes_valides)
    print("\nFin.")


if __name__ == "__main__":
    main()
