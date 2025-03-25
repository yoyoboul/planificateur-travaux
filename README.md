# Planificateur de Travaux

Une application interactive pour visualiser, organiser et planifier des travaux de rénovation d'appartement.

## Fonctionnalités

- Vue d'ensemble des travaux par zone
- Visualisation détaillée des tâches
- Planification via un agenda interactif
- Suivi de l'avancement des travaux

## Installation

1. Cloner ce dépôt
2. Installer les dépendances:
   ```
   pip install -r requirements.txt
   ```
3. Lancer l'application:
   ```
   streamlit run app.py
   ```

## Structure du projet

- `app.py` : Point d'entrée de l'application
- `data.py` : Gestion des données des travaux
- `utils.py` : Fonctions utilitaires
- `visualisation.py` : Composants de visualisation
- `agenda.py` : Fonctionnalités d'agenda

## Utilisation

1. Consultez la vue d'ensemble pour voir toutes les zones de travaux
2. Explorez les détails de chaque zone
3. Planifiez vos travaux dans l'agenda
4. Suivez votre progression au fil du temps 