"""
Gestionnaire de configuration pour l'application Planificateur de Travaux.
Permet de basculer entre le stockage JSON et SQLite.
"""

import os

# Fichier de configuration
CONFIG_FILE = '.db_config'

def use_sqlite():
    """Vérifie si l'application doit utiliser SQLite ou JSON"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            content = f.read().strip()
            return 'use_sqlite=True' in content
    return False

def set_storage_mode(use_sqlite_mode=True):
    """Définit le mode de stockage de l'application"""
    with open(CONFIG_FILE, 'w') as f:
        if use_sqlite_mode:
            f.write('use_sqlite=True\n')
        else:
            f.write('use_sqlite=False\n')
    return True 