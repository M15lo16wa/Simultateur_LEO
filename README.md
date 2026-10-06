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

## Remarque

Le projet mentionne aussi un module externe `LEOCraft` pour la visualisation, qui n'est pas publié sur PyPI. Si nécessaire, il faut le cloner séparément et l'ajouter au `PYTHONPATH`.
