import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

# Chemin de la base de données
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks.db')

def init_db():
    """Initialise la base de données si elle n'existe pas"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Créer la table des zones si elle n'existe pas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS zones (
        id INTEGER PRIMARY KEY,
        nom TEXT UNIQUE
    )
    ''')
    
    # Créer la table des tâches si elle n'existe pas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS taches (
        id INTEGER PRIMARY KEY,
        zone_id INTEGER,
        titre TEXT,
        statut TEXT,
        priorite TEXT,
        duree_estimee REAL,
        date_debut TEXT,
        date_fin TEXT,
        FOREIGN KEY (zone_id) REFERENCES zones (id),
        UNIQUE (zone_id, titre)
    )
    ''')
    
    # Vérifier si les zones par défaut existent déjà
    cursor.execute("SELECT COUNT(*) FROM zones")
    if cursor.fetchone()[0] == 0:
        # Insérer les zones par défaut
        default_zones = ["Palier", "Cuisine/Séjour", "Escalier", "Cuisine"]
        for zone in default_zones:
            cursor.execute("INSERT INTO zones (nom) VALUES (?)", (zone,))
    
    conn.commit()
    conn.close()

# Initialiser la base de données au démarrage
init_db()

def get_all_tasks():
    """Retourne toutes les tâches dans un DataFrame pandas"""
    conn = sqlite3.connect(DB_FILE)
    
    query = '''
    SELECT 
        t.id, z.nom as zone, t.titre, t.statut, t.priorite as priorité, 
        t.duree_estimee as durée_estimée, t.date_debut as date_début, 
        t.date_fin as date_fin
    FROM taches t
    JOIN zones z ON t.zone_id = z.id
    '''
    
    # Charger les données dans un DataFrame
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convertir les dates si elles existent
    if not df.empty:
        if 'date_début' in df.columns:
            df['date_début'] = pd.to_datetime(df['date_début'])
        if 'date_fin' in df.columns:
            df['date_fin'] = pd.to_datetime(df['date_fin'])
    
    return df

def get_tasks_by_zone(zone):
    """Retourne les tâches d'une zone spécifique"""
    conn = sqlite3.connect(DB_FILE)
    
    query = '''
    SELECT 
        t.id, t.titre, t.statut, t.priorite as priorité, 
        t.duree_estimee as durée_estimée, t.date_debut as date_début, 
        t.date_fin as date_fin
    FROM taches t
    JOIN zones z ON t.zone_id = z.id
    WHERE z.nom = ?
    '''
    
    # Charger les données dans un DataFrame
    df = pd.read_sql_query(query, conn, params=(zone,))
    conn.close()
    
    # Convertir les dates si elles existent
    if not df.empty:
        if 'date_début' in df.columns:
            df['date_début'] = pd.to_datetime(df['date_début'])
        if 'date_fin' in df.columns:
            df['date_fin'] = pd.to_datetime(df['date_fin'])
    
    return df

def get_zones():
    """Retourne la liste des zones de travaux"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT nom FROM zones ORDER BY id")
    zones = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return zones

def count_tasks_by_status():
    """Compte le nombre de tâches par statut"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT statut, COUNT(*) FROM taches GROUP BY statut")
    result = {status: count for status, count in cursor.fetchall()}
    
    conn.close()
    return result

def count_tasks_by_zone():
    """Compte le nombre de tâches par zone"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT z.nom, COUNT(t.id) 
    FROM zones z 
    LEFT JOIN taches t ON z.id = t.zone_id 
    GROUP BY z.nom
    """)
    result = {zone: count for zone, count in cursor.fetchall()}
    
    conn.close()
    return result

def update_task_status(zone, task_title, new_status):
    """Met à jour le statut d'une tâche"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE taches 
    SET statut = ? 
    WHERE titre = ? AND zone_id = (SELECT id FROM zones WHERE nom = ?)
    """, (new_status, task_title, zone))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_affected > 0

def schedule_task(zone, task_title, start_date, custom_duration=None):
    """Planifie une tâche à une date spécifique"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # D'abord, obtenez la durée actuelle si aucune durée personnalisée n'est fournie
    if custom_duration is None:
        cursor.execute("""
        SELECT duree_estimee 
        FROM taches 
        WHERE titre = ? AND zone_id = (SELECT id FROM zones WHERE nom = ?)
        """, (task_title, zone))
        result = cursor.fetchone()
        if result:
            custom_duration = result[0]
        else:
            conn.close()
            return False
    
    # Calcul de la date de fin
    end_date = start_date + timedelta(days=custom_duration)
    
    # Mettre à jour la tâche
    cursor.execute("""
    UPDATE taches 
    SET date_debut = ?, date_fin = ?, duree_estimee = ? 
    WHERE titre = ? AND zone_id = (SELECT id FROM zones WHERE nom = ?)
    """, (start_date.isoformat(), end_date.isoformat(), custom_duration, task_title, zone))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_affected > 0

def unschedule_task(zone, task_title):
    """Supprime la planification d'une tâche"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE taches 
    SET date_debut = NULL, date_fin = NULL
    WHERE titre = ? AND zone_id = (SELECT id FROM zones WHERE nom = ?)
    """, (task_title, zone))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_affected > 0

def get_scheduled_tasks():
    """Retourne toutes les tâches planifiées"""
    conn = sqlite3.connect(DB_FILE)
    
    query = '''
    SELECT 
        t.id, z.nom as zone, t.titre, t.statut, t.priorite as priorité, 
        t.duree_estimee as durée_estimée, t.date_debut as date_début, 
        t.date_fin as date_fin
    FROM taches t
    JOIN zones z ON t.zone_id = z.id
    WHERE t.date_debut IS NOT NULL AND t.date_fin IS NOT NULL
    '''
    
    # Charger les données dans un DataFrame
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convertir les dates
    if not df.empty:
        df['date_début'] = pd.to_datetime(df['date_début'])
        df['date_fin'] = pd.to_datetime(df['date_fin'])
    
    return df

def add_task(zone, titre, priorite="Moyenne", duree_estimee=1.0, statut="À faire"):
    """Ajoute une nouvelle tâche dans une zone spécifique"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Récupérer l'id de la zone
        cursor.execute("SELECT id FROM zones WHERE nom = ?", (zone,))
        zone_id = cursor.fetchone()
        
        if not zone_id:
            # La zone n'existe pas, créons-la
            cursor.execute("INSERT INTO zones (nom) VALUES (?)", (zone,))
            zone_id = cursor.lastrowid
        else:
            zone_id = zone_id[0]
        
        # Insérer la nouvelle tâche
        cursor.execute("""
        INSERT INTO taches (zone_id, titre, statut, priorite, duree_estimee)
        VALUES (?, ?, ?, ?, ?)
        """, (zone_id, titre, statut, priorite, duree_estimee))
        
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # Une tâche avec ce titre existe déjà dans cette zone
        conn.rollback()
        success = False
    except Exception as e:
        print(f"Erreur lors de l'ajout de la tâche: {e}")
        conn.rollback()
        success = False
    finally:
        conn.close()
    
    return success

def delete_task(zone, task_title):
    """Supprime une tâche d'une zone spécifique"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
    DELETE FROM taches 
    WHERE titre = ? AND zone_id = (SELECT id FROM zones WHERE nom = ?)
    """, (task_title, zone))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_affected > 0

def reset_to_empty():
    """Réinitialise la base de données en supprimant toutes les tâches"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM taches")
    
    conn.commit()
    conn.close()
    return True

# Fonction pour migrer les données du JSON vers SQLite
def migrate_from_json(json_file):
    """Migre les données d'un fichier JSON vers la base de données SQLite"""
    import json
    
    try:
        # Charger les données JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Vider la base de données existante
        reset_to_empty()
        
        # Ajouter chaque tâche à la base de données
        for zone, taches in data.items():
            for tache in taches:
                # Ajouter la tâche
                add_task(
                    zone=zone,
                    titre=tache["titre"],
                    priorite=tache["priorité"],
                    duree_estimee=tache["durée_estimée"],
                    statut=tache["statut"]
                )
                
                # Si la tâche est planifiée, ajouter les dates
                if "date_début" in tache and "date_fin" in tache:
                    date_debut = datetime.fromisoformat(tache["date_début"])
                    schedule_task(
                        zone=zone,
                        task_title=tache["titre"],
                        start_date=date_debut,
                        custom_duration=tache["durée_estimée"]
                    )
        
        return True
    except Exception as e:
        print(f"Erreur lors de la migration: {e}")
        return False 