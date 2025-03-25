#!/usr/bin/env python3
"""
Script de migration des données JSON vers SQLite pour l'application Planificateur de Travaux.
À exécuter une seule fois pour passer au nouveau système de stockage.
"""

import os
import sys
import json
import time

# Vérifier si le fichier de configuration existe
CONFIG_FILE = '.db_config'
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        if 'use_sqlite=True' in f.read():
            print("La migration a déjà été effectuée.")
            sys.exit(0)

# Vérifier si le fichier JSON existe
DATA_FILE = 'tasks_data.json'
if not os.path.exists(DATA_FILE):
    print(f"Fichier {DATA_FILE} introuvable.")
    sys.exit(1)

print("Migration des données de JSON vers SQLite...")
print("Chargement des données JSON...")

try:
    # Import du module db
    import db
    
    # Migrer les données
    success = db.migrate_from_json(DATA_FILE)
    
    if success:
        print("Migration réussie!")
        
        # Créer un fichier de configuration
        with open(CONFIG_FILE, 'w') as f:
            f.write('use_sqlite=True\n')
        
        # Créer une sauvegarde du fichier JSON
        backup_file = f"{DATA_FILE}.bak.{int(time.time())}"
        print(f"Création d'une sauvegarde du fichier JSON: {backup_file}")
        
        with open(DATA_FILE, 'r', encoding='utf-8') as src:
            with open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        print("La migration est terminée. Vous pouvez maintenant utiliser SQLite.")
        print("Pour revenir à JSON, supprimez le fichier .db_config.")
    else:
        print("Échec de la migration. Vérifiez les erreurs ci-dessus.")
except Exception as e:
    print(f"Erreur lors de la migration: {e}")
    sys.exit(1) 