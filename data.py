"""
Module de gestion des données des travaux de rénovation
"""
import pandas as pd
from datetime import datetime, timedelta
import json
import os

# Définir le chemin du fichier de données
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks_data.json')

# Structure vide pour les travaux (sans données initiales)
EMPTY_TRAVAUX = {
    "Palier": [],
    "Cuisine/Séjour": [],
    "Escalier": [],
    "Cuisine": []
}

# Initialiser la variable TRAVAUX globale
TRAVAUX = {}

# Charger les données sauvegardées ou utiliser une structure vide
def load_data():
    """Charge les données depuis le fichier JSON ou initialise une structure vide"""
    global TRAVAUX
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                # Convertir les objets datetime en chaînes lors du chargement
                data = json.load(f)
                TRAVAUX = data
                
                # Reconvertir les chaînes de date en objets datetime si nécessaire
                for zone, taches in TRAVAUX.items():
                    for tache in taches:
                        if "date_début" in tache and isinstance(tache["date_début"], str):
                            tache["date_début"] = datetime.fromisoformat(tache["date_début"])
                        if "date_fin" in tache and isinstance(tache["date_fin"], str):
                            tache["date_fin"] = datetime.fromisoformat(tache["date_fin"])
        else:
            # Si le fichier n'existe pas, initialiser avec une structure vide
            TRAVAUX = EMPTY_TRAVAUX.copy()
            save_data()  # Créer le fichier pour la première fois
    except Exception as e:
        print(f"Erreur lors du chargement des données: {e}")
        # En cas d'erreur, initialiser avec une structure vide
        TRAVAUX = EMPTY_TRAVAUX.copy()
        save_data()  # Recréer le fichier

# Sauvegarder les données dans un fichier JSON
def save_data():
    """Sauvegarde les données dans un fichier JSON"""
    try:
        # Créer une copie des données pour la sérialisation
        data_to_save = {}
        for zone, taches in TRAVAUX.items():
            data_to_save[zone] = []
            for tache in taches:
                tache_copy = tache.copy()
                # Convertir les objets datetime en chaînes
                if "date_début" in tache_copy and isinstance(tache_copy["date_début"], datetime):
                    tache_copy["date_début"] = tache_copy["date_début"].isoformat()
                if "date_fin" in tache_copy and isinstance(tache_copy["date_fin"], datetime):
                    tache_copy["date_fin"] = tache_copy["date_fin"].isoformat()
                data_to_save[zone].append(tache_copy)
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données: {e}")

# Initialiser les données au démarrage
load_data()

def get_all_tasks():
    """Retourne toutes les tâches dans un DataFrame pandas"""
    tasks = []
    for zone, taches in TRAVAUX.items():
        for tache in taches:
            task_info = tache.copy()
            task_info['zone'] = zone
            tasks.append(task_info)
    return pd.DataFrame(tasks)

def get_tasks_by_zone(zone):
    """Retourne les tâches d'une zone spécifique"""
    if zone in TRAVAUX:
        return pd.DataFrame(TRAVAUX[zone])
    return pd.DataFrame()

def get_zones():
    """Retourne la liste des zones de travaux"""
    return list(TRAVAUX.keys())

def count_tasks_by_status():
    """Compte le nombre de tâches par statut"""
    df = get_all_tasks()
    if df.empty:
        return {}
    return df['statut'].value_counts().to_dict()

def count_tasks_by_zone():
    """Compte le nombre de tâches par zone"""
    return {zone: len(tasks) for zone, tasks in TRAVAUX.items()}

def update_task_status(zone, task_title, new_status):
    """Met à jour le statut d'une tâche"""
    for tache in TRAVAUX[zone]:
        if tache["titre"] == task_title:
            tache["statut"] = new_status
            save_data()  # Sauvegarder les modifications
            return True
    return False

def schedule_task(zone, task_title, start_date, custom_duration=None):
    """Planifie une tâche à une date spécifique"""
    for tache in TRAVAUX[zone]:
        if tache["titre"] == task_title:
            tache["date_début"] = start_date
            
            # Utiliser la durée personnalisée si fournie, sinon utiliser la durée estimée par défaut
            duration = custom_duration if custom_duration is not None else tache["durée_estimée"]
            
            # Si une durée personnalisée est fournie, la mettre à jour dans les données
            if custom_duration is not None:
                tache["durée_estimée"] = custom_duration
                
            # Calcul de la date de fin en fonction de la durée
            end_date = start_date + timedelta(days=duration)
            tache["date_fin"] = end_date
            save_data()  # Sauvegarder les modifications
            return True
    return False

def unschedule_task(zone, task_title):
    """Supprime la planification d'une tâche (retire les dates de début et de fin)
    
    Paramètres:
    - zone: la zone où se trouve la tâche
    - task_title: le titre de la tâche à déplanifier
    
    Retourne:
    - True si la déplanification a réussi
    - False sinon
    """
    for tache in TRAVAUX[zone]:
        if tache["titre"] == task_title:
            # Supprimer les dates de début et de fin si elles existent
            if "date_début" in tache:
                del tache["date_début"]
            if "date_fin" in tache:
                del tache["date_fin"]
            save_data()  # Sauvegarder les modifications
            return True
    return False

def get_scheduled_tasks():
    """Retourne toutes les tâches planifiées"""
    tasks = []
    for zone, taches in TRAVAUX.items():
        for tache in taches:
            if "date_début" in tache and "date_fin" in tache:
                task_info = tache.copy()
                task_info['zone'] = zone
                tasks.append(task_info)
    return pd.DataFrame(tasks)

def add_task(zone, titre, priorite="Moyenne", duree_estimee=1.0, statut="À faire"):
    """Ajoute une nouvelle tâche dans une zone spécifique
    
    Paramètres:
    - zone: la zone où ajouter la tâche
    - titre: le titre de la nouvelle tâche
    - priorite: la priorité de la tâche (Élevée, Moyenne, Basse, Faible)
    - duree_estimee: la durée estimée en jours
    - statut: le statut initial (À faire, En cours, En attente, Terminé)
    
    Retourne:
    - True si l'ajout a réussi
    - False sinon
    """
    if zone not in TRAVAUX:
        return False
        
    # Vérifier si une tâche avec le même titre existe déjà
    for tache in TRAVAUX[zone]:
        if tache["titre"] == titre:
            return False
    
    # Créer la nouvelle tâche
    nouvelle_tache = {
        "titre": titre,
        "statut": statut,
        "priorité": priorite,
        "durée_estimée": duree_estimee
    }
    
    # Ajouter la tâche à la zone
    TRAVAUX[zone].append(nouvelle_tache)
    save_data()  # Sauvegarder les modifications
    return True

def delete_task(zone, task_title):
    """Supprime une tâche d'une zone spécifique
    
    Paramètres:
    - zone: la zone où se trouve la tâche
    - task_title: le titre de la tâche à supprimer
    
    Retourne:
    - True si la suppression a réussi
    - False sinon
    """
    if zone not in TRAVAUX:
        return False
    
    # Trouver l'index de la tâche à supprimer
    for i, tache in enumerate(TRAVAUX[zone]):
        if tache["titre"] == task_title:
            # Supprimer la tâche
            TRAVAUX[zone].pop(i)
            save_data()  # Sauvegarder les modifications
            return True
    
    return False

def reset_to_empty():
    """Réinitialise les données à une structure vide"""
    global TRAVAUX
    TRAVAUX = EMPTY_TRAVAUX.copy()
    save_data()
    return True 