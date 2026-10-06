# Simulateur LEO

C'est un simulateur Python pour la simulation de performance de l'architecture des constellation LEO.

Le projet permet d'estimer la visibilité des satellites, le RTT, le handover, le Doppler et le bilan de liaison pour une station au sol dans le cadre d'une constellation LEO (type Starlink).

## Prérequis

- Python 3.11 ou plus
- pip
- Git

## Clonage du projet

```bash
git clone https://github.com/M15lo16wa/Simultateur_LEO.git
cd Simultateur_LEO
```

## Installation

Créez un environnement virtuel puis installez les dépendances :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Sous Windows PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

Le script charge les satellites depuis CelesTrak, analyse leur visibilité et lance l'interface visuelle du simulateur.

## Critères d'évaluation du résultat

Les résultats de la simulation sont évalués selon les critères suivants :

### Visibilité des satellites
- **Angle d'élévation minimum** : Les satellites doivent dépasser un seuil d'élévation (généralement 10°-20°) pour être considérés comme visibles
- **Fenêtre de visibilité** : Durée maximale pendant laquelle un satellite reste visible depuis la station au sol
- **Nombre de satellites visibles** : Le nombre simultané de satellites en vue

### RTT (Round-Trip Time)
- **RTT minimal et maximal** : Évaluation de la latence minimum et maximum observée
- **RTT moyen** : Latence moyenne au cours de la visibilité du satellite
- **Stabilité du RTT** : Variation de la latence au fil du temps

### Handover
- **Fréquence des handovers** : Nombre de transferts de satellites au cours d'une session
- **Durée de transition** : Temps pour basculer d'un satellite à un autre
- **Continuité de service** : Absence de rupture de connexion pendant le handover

### Effet Doppler
- **Décalage Doppler maximal** : Décalage maximum de fréquence observé
- **Signe du décalage** : Décalage positif (approche) ou négatif (éloignement)
- **Gradient Doppler** : Vitesse de variation du décalage Doppler

### Bilan de liaison (Link Budget)
- **SINR (Signal-to-Interference-plus-Noise Ratio)** : Rapport signal/bruit adéquat (> 5 dB recommandé)
- **Marge de connexion** : Différence entre le SINR requis et le SINR disponible
- **Atténuation du signal** : Perte de signal due à la distance et aux conditions atmosphériques

## Remarque

Le projet mentionne aussi un module externe `LEOCraft` pour la visualisation, qui n'est pas publié sur PyPI. Si nécessaire, il faut le cloner séparément et l'ajouter au `PYTHONPATH`.
