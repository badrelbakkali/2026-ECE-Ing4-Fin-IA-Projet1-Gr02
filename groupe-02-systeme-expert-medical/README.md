# Système expert médical (programmation logique)

Prototype pédagogique de **système expert médical** basé sur une **base de connaissances** (règles + symptômes) et un **moteur d’inférence** (chaînage avant / arrière) avec **gestion d’incertitude** (facteurs de confiance).  

## Fonctionnalités

- **Moteur d’inférence**
  - Chaînage **avant** (déduction à partir des symptômes)
  - Chaînage **arrière** (validation par diagnostic cible)
- **Base de connaissances** en JSON
  - Symptômes + catégories (ORL, digestif, etc.)
  - Règles `si_tous` / `si_un` avec facteur de confiance
- **Gestion d’incertitude**
  - Score par diagnostic ∈ [0, 1]
  - Combinaison progressive des contributions de règles
- **Interface Web**
  - UI dynamique : la liste des symptômes/catégories est chargée depuis l’API (`/config`)
  - Affichage des top diagnostics, explications, debug payload

---

## Arborescence

groupe-02-systeme-expert-medical/
├── src/
│ ├── base_connaissances.json
│ └── moteur_inference.py
├── web/
│ ├── backend/
│ │ └── app.py
│ └── frontend/
│ └── index.html
├── docs/
└── slides/


---

## Installation

### Prérequis
- Python **3.10+** (recommandé : 3.11)
- Navigateur web (Chrome/Edge/Firefox)

### Dépendances Python
Depuis la racine du dépôt (ou depuis `groupe-02-systeme-expert-medical/`, selon ta config) :

```bash
pip install fastapi uvicorn
Optionnel (si besoin selon ton environnement) :
pip install "uvicorn[standard]"

---
## Lancement
1) Lancer l’API (backend)

Depuis la racine du dépôt :
python -m uvicorn groupe-02-systeme-expert-medical.web.backend.app:app --reload --port 8000

L’API est disponible sur :
http://127.0.0.1:8000


Endpoints utiles :

GET /config → symptômes + catégories + labels diagnostics

POST /diagnostic → inférence + top résultats

2) Lancer le frontend

Ouvrir le fichier suivant dans le navigateur :

groupe-02-systeme-expert-medical/web/frontend/index.html

Si ton navigateur bloque certains fetch en local, tu peux utiliser un serveur statique :
python -m http.server 5500
Puis ouvrir :
http://127.0.0.1:5500/groupe-02-systeme-expert-medical/web/frontend/index.html


### Utilisation

1) Choisir le mode d’inférence (chaînage avant/arrière)
2) Cocher des symptômes (groupés par catégories)
3) Cliquer sur Diagnostiquer
4) Lire :
    -diagnostics (Top 3)
    -score + niveau de certitude
    -explications des règles activées
    -suggestions de symptômes pour affiner (si présentes)


 ### Exemples de tests (cas de démonstration)

Grippe (diagnostic élevé)
Coche : fievre, frissons, courbatures, fatigue, maux_de_tete, toux_seche
Attendu : Grippe en top avec score élevé

Migraine (diagnostic élevé)
Coche : maux_de_tete, sensibilite_lumiere, nausees, douleur_un_cote_tete, aggravation_effort
Attendu : Migraine en top avec score élevé

Cystite (diagnostic élevé)
Coche : brulures_urinaires, envies_frequentes_uriner, douleur_bas_ventre, urines_troubles
Attendu : Cystite en top avec score élevé

Cas ambigu (incertitude)
Coche : maux_de_tete, fatigue
Attendu : score modéré, diagnostic non spécifique / incertitude visible



### Détails techniques
Base de connaissances (JSON)
Chaque règle suit le format :
-si_tous : symptômes obligatoires (AND)
-si_un : symptômes optionnels (OR, au moins 1 si la liste existe)
-confiance : coefficient [0..1]
-explication : phrase affichée à l’utilisateur
Exemple : 
{
  "id": "r_grippe_1",
  "diagnostic": "grippe",
  "si_tous": ["fievre", "frissons"],
  "si_un": ["courbatures", "fatigue", "maux_de_tete", "toux_seche"],
  "confiance": 0.72,
  "explication": "Fièvre et frissons avec symptômes généraux évoquent une grippe."
}

#Calcul du score
-Pour une règle applicable, on calcule une contribution score_ajoute basée sur :
    la confiance de la règle
    un bonus proportionnel selon le nombre de symptômes optionnels présents (si_un)
-Les contributions se combinent avec une formule de type “cumul probabiliste” :
    score = 1 - (1 - score) * (1 - score_ajoute)

Ce mécanisme évite de dépasser 1 et permet à plusieurs règles de renforcer progressivement un diagnostic.

###Limites
-Prototype pédagogique, règles simplifiées
-Les symptômes/diagnostics ne couvrent pas toutes les pathologies
-Les scores ne constituent pas une probabilité médicale réelle
-Ne pas utiliser pour une décision clinique

###Auteurs

FINANCE Groupe 02 — Systèmes experts médicaux en programmation logique

Membres : 
El Bakkali Badr : badrelbakkali
El Yousoufi Zakaria : zakariaelyousoufi
Id El Ouali Kawthar : Kaihiiro