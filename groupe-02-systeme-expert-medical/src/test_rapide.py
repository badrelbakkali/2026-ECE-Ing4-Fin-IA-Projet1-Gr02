from moteur_inference import (
    charger_base_connaissances,
    inferer_diagnostics,
    top_k,
    filtrer_symptomes_inconnus,
)

BASE = "groupe-02-systeme-expert-medical/src/base_connaissances.json"


def afficher_resultats(symptomes):
    base = charger_base_connaissances(BASE)

    symptomes_valides, inconnus = filtrer_symptomes_inconnus(base, set(symptomes))
    if inconnus:
        print("Symptômes inconnus ignorés:", sorted(list(inconnus)))

    scores, traces = inferer_diagnostics(base, symptomes_valides)

    print("Symptômes donnés:", symptomes)
    print("\nTop diagnostics:")

    for diag, score in top_k(scores, k=3):
        print(f"- {diag} : {score:.3f}")
        if diag in traces:
            print("  règles déclenchées :")
            for m in traces[diag]:
                print(f"   • {m.regle_id} | +{m.score_ajoute:.3f} | {m.explication}")
        print()

    print("\n---\n")


if __name__ == "__main__":
    afficher_resultats(["fievre", "fatigue", "courbatures", "frissons", "toux"])
    afficher_resultats(["nez_qui_coule", "eternuements", "mal_de_gorge"])
    afficher_resultats(["brulures_urinaires", "envies_frequentes_uriner", "urines_troubles"])
    afficher_resultats(["maux_de_tete", "douleur_un_cote_tete", "sensibilite_lumiere", "nausees"])
