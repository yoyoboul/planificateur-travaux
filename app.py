"""
Application de planification des travaux de rénovation
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys
import time

# Configuration de la page Streamlit - DOIT ÊTRE LA PREMIÈRE COMMANDE STREAMLIT
st.set_page_config(
    page_title="Planificateur de Travaux",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Vérifier quel mode de stockage utiliser
    import config_manager
    if config_manager.use_sqlite():
        import db as data
        # Ces informations seront affichées plus tard dans main()
        storage_mode = "SQLite (Base de données)"
        storage_mode_is_sqlite = True
    else:
        import data
        storage_mode = "JSON (Fichier plat)"
        storage_mode_is_sqlite = False
        
    import visualisation
    import agenda
    import utils
except ImportError as e:
    st.error(f"Erreur d'importation: {e}")
    st.info("Assurez-vous d'avoir installé toutes les dépendances nécessaires avec `pip install -r requirements.txt`")
    st.stop()

# Ajout des méta-balises pour améliorer l'affichage sur mobile
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0">
""", unsafe_allow_html=True)

# Styles CSS personnalisés pour l'application avec optimisation mobile
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .section-header {
        font-size: 1.8rem;
        color: #333;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    .card {
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .zone-title {
        font-weight: bold;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        display: inline-block;
        margin-bottom: 10px;
    }
    
    .stProgressBar {
        height: 10px;
    }
    
    .stProgress > div > div {
        background-color: #4CAF50;
    }
    
    .task-list {
        margin-top: 15px;
    }
    
    .footer {
        margin-top: 3rem;
        text-align: center;
        font-size: 0.8rem;
        color: #666;
    }
    
    /* Optimisations pour les appareils mobiles */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
        }
        
        .section-header {
            font-size: 1.4rem;
            margin-top: 1.5rem;
            margin-bottom: 0.8rem;
        }
        
        .card {
            padding: 0.8rem;
            margin-bottom: 0.8rem;
        }
        
        /* Réduire la taille des boutons sur mobile */
        button {
            font-size: 0.9rem !important;
            padding: 0.3rem 0.5rem !important;
        }
        
        /* Ajuster les colonnes pour mobile */
        .mobile-full-width {
            width: 100% !important;
            flex: 1 1 100% !important;
            max-width: 100% !important;
        }
        
        /* Ajuster l'espacement */
        .row-widget.stButton {
            margin-bottom: 0.5rem;
        }
        
        /* Améliorations pour la sidebar sur mobile */
        [data-testid="stSidebar"] {
            width: 100%;
            min-width: 0;
        }
        
        /* Rendre les sélecteurs plus grands pour les doigts */
        .stSelectbox, .stDateInput {
            min-height: 40px;
        }
        
        [data-baseweb="select"] {
            min-height: 40px;
        }
    }
    
    /* Classe utilitaire pour détecter et adapter le contenu sur mobile */
    .mobile-container {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
    }
</style>
""", unsafe_allow_html=True)

# Script JavaScript pour détecter les appareils mobiles et ajuster l'interface
st.markdown("""
<script>
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    if (isMobile) {
        // Ajouter une classe 'mobile' au body pour cibler avec CSS
        document.body.classList.add('mobile-view');
        
        // Réduire les marges et paddings pour optimiser l'espace
        document.querySelectorAll('.stApp').forEach(el => {
            el.style.padding = '0.5rem';
        });
    }
</script>
""", unsafe_allow_html=True)

def main():
    """Fonction principale de l'application"""
    try:
        # Barre latérale avec les sections principales
        st.sidebar.markdown("<h1 style='text-align: center;'>🏠 Planificateur</h1>", unsafe_allow_html=True)
        
        # Afficher le mode de stockage dans la barre latérale
        if storage_mode_is_sqlite:
            st.sidebar.success(f"Mode de stockage: {storage_mode}")
        else:
            st.sidebar.info(f"Mode de stockage: {storage_mode}")
        
        # Menu de navigation
        page = st.sidebar.radio(
            "Navigation",
            ["Tableau de bord", "Liste des travaux", "Agenda", "Rapport", "Gérer les tâches"]
        )
        
        # Section d'administration (cachée par défaut)
        with st.sidebar.expander("⚙️ Administration"):
            st.write("Options avancées pour la gestion des données")
            
            # Afficher le mode de stockage actuel
            current_mode = "SQLite" if config_manager.use_sqlite() else "JSON"
            st.write(f"**Mode actuel:** {current_mode}")
            
            # Option pour migrer de JSON vers SQLite
            if not config_manager.use_sqlite():
                if st.button("Migrer vers SQLite"):
                    with st.spinner("Migration en cours..."):
                        import subprocess
                        result = subprocess.run(["python3", "migration.py"], capture_output=True, text=True)
                        if "Migration réussie" in result.stdout:
                            st.success("Migration vers SQLite réussie! Redémarrage...")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"Échec de la migration: {result.stdout}\n{result.stderr}")
            
            # Option pour revenir à JSON
            else:
                if st.button("Revenir au stockage JSON"):
                    if st.session_state.get("confirm_json_switch", False):
                        # Confirmer la conversion
                        config_manager.set_storage_mode(False)
                        st.success("Retour au stockage JSON. Redémarrage...")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.session_state["confirm_json_switch"] = True
                        st.warning("⚠️ Attention: Cette opération est réversible mais vos dernières modifications dans SQLite pourraient être perdues. Cliquez à nouveau pour confirmer.")
            
            # Option pour réinitialiser les données
            if st.button("Réinitialiser toutes les données"):
                if st.session_state.get("confirm_reset", False):
                    # Confirmer la réinitialisation
                    if config_manager.use_sqlite():
                        import db
                        db.reset_to_empty()
                    else:
                        data.reset_to_empty()
                    st.success("Données réinitialisées avec succès. Redémarrage...")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.session_state["confirm_reset"] = True
                    st.warning("⚠️ Attention: Cette opération supprimera toutes vos données! Cliquez à nouveau pour confirmer.")
        
        # Afficher différent selon la page sélectionnée
        if page == "Tableau de bord":
            display_dashboard()
        elif page == "Liste des travaux":
            display_task_list()
        elif page == "Agenda":
            agenda.display_agenda()
        elif page == "Rapport":
            display_report()
        elif page == "Gérer les tâches":
            manage_tasks()
        
        # Pied de page
        st.markdown("""
        <div class="footer">
            Planificateur de Travaux de Rénovation - Développé avec Streamlit
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Une erreur s'est produite: {e}")
        import traceback
        st.code(traceback.format_exc())

def display_todays_tasks():
    """Affiche les tâches planifiées pour aujourd'hui"""
    # Obtenir toutes les tâches planifiées
    scheduled_tasks = data.get_scheduled_tasks()
    
    if scheduled_tasks.empty:
        st.info("Aucune tâche n'est actuellement planifiée dans l'agenda.")
        return
    
    # Obtenir la date d'aujourd'hui
    today = datetime.now().date()
    
    # Filtrer les tâches pour aujourd'hui
    todays_tasks = []
    for _, task in scheduled_tasks.iterrows():
        if task["date_début"].date() <= today <= task["date_fin"].date():
            todays_tasks.append(task)
    
    # Afficher les tâches d'aujourd'hui
    if todays_tasks:
        st.markdown("<h3 style='color: #1E88E5;'>📅 Tâches d'aujourd'hui</h3>", unsafe_allow_html=True)
        
        # Créer un conteneur avec un style
        task_container = st.container()
        with task_container:
            st.markdown("""
            <style>
            .today-task {
                background-color: #f0f7ff;
                border-left: 4px solid #1E88E5;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 4px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Afficher chaque tâche
            for task in todays_tasks:
                task_html = f"""
                <div class="today-task">
                    <strong>{task['titre']}</strong> ({task['zone']})
                    <br>
                    <span style="color: {'green' if task['statut'] == 'Terminé' else 'orange'};">
                        {task['statut']} - Priorité {task['priorité']}
                    </span>
                </div>
                """
                st.markdown(task_html, unsafe_allow_html=True)
    else:
        st.info("Aucune tâche planifiée pour aujourd'hui.")
        st.write("Utilisez l'agenda pour planifier des tâches.")

def display_dashboard():
    """Affiche le tableau de bord principal"""
    st.markdown("<h1 class='main-header'>Tableau de Bord des Travaux</h1>", unsafe_allow_html=True)
    
    # Obtenir les données des tâches
    all_tasks = data.get_all_tasks()
    
    # Vérifier si toutes les tâches ont été supprimées
    if all_tasks.empty:
        st.warning("❗ Aucune tâche n'a été trouvée dans le système.")
        st.info("Utilisez la page 'Gérer les tâches' pour ajouter de nouvelles tâches.")
        
        # Bouton pour aller directement à la page de gestion des tâches
        if st.button("Ajouter des tâches"):
            st.session_state.page = "Gérer les tâches"
            st.rerun()
        return
    
    # Détection des appareils mobiles (à utiliser pour adapter la mise en page)
    # Streamlit ne peut pas directement détecter les appareils mobiles côté serveur,
    # mais nous pouvons utiliser la largeur d'écran comme proxy
    screen_width = st.session_state.get('_screen_width', 1200)  # Valeur par défaut desktop
    is_mobile = screen_width < 768  # Considère comme mobile si écran < 768px
    
    # Ajoutons un widget caché qui va tenter de mesurer la largeur d'écran via JavaScript
    st.markdown("""
    <div style="display:none" id="screen_width_detector">
        <script>
            // Envoi de la largeur d'écran à Streamlit
            const screenWidth = window.innerWidth;
            const widthElement = document.getElementById('screen_width_detector');
            widthElement.textContent = screenWidth;
            
            // Créer une fonction pour mettre à jour la largeur lors du redimensionnement
            function updateWidth() {
                const newWidth = window.innerWidth;
                widthElement.textContent = newWidth;
            }
            
            // Écouter les événements de redimensionnement
            window.addEventListener('resize', updateWidth);
        </script>
    </div>
    """, unsafe_allow_html=True)
    
    # Afficher les métriques principales - Style adaptatif selon le type d'appareil
    if is_mobile:
        # Disposition verticale pour mobile
        col1 = st.container()
        col2 = st.container()
        col3 = st.container()
        col4 = st.container()
    else:
        # Disposition horizontale pour desktop
        col1, col2, col3, col4 = st.columns(4)
    
    # Nombre total de tâches
    total_tasks = len(all_tasks)
    col1.metric("Total des tâches", total_tasks)
    
    # Tâches par statut
    tasks_by_status = data.count_tasks_by_status()
    completed = tasks_by_status.get("Terminé", 0)
    in_progress = tasks_by_status.get("En cours", 0)
    pending = tasks_by_status.get("En attente", 0)
    
    col2.metric("Terminées", completed)
    col3.metric("En cours", in_progress)
    col4.metric("En attente", pending)
    
    # Barre de progression globale
    completion_percentage = (completed / total_tasks) * 100 if total_tasks > 0 else 0
    st.markdown("### Progression globale")
    st.progress(completion_percentage / 100)
    st.write(f"{completion_percentage:.1f}% terminé")
    
    # Afficher les tâches d'aujourd'hui
    display_todays_tasks()
    
    # Afficher les graphiques de visualisation - adaptatif selon l'appareil
    if is_mobile:
        # Sur mobile, afficher les graphiques en pleine largeur, un au-dessus de l'autre
        st.subheader("Répartition par zone")
        tasks_by_zone = data.count_tasks_by_zone()
        fig = visualisation.create_task_overview_chart(tasks_by_zone)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Statut des tâches")
        fig = visualisation.create_task_status_chart(tasks_by_status)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Répartition par priorité")
        fig = visualisation.create_priority_chart(all_tasks)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Progression dans le temps")
        fig = visualisation.create_burndown_chart(all_tasks)
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Sur desktop, afficher les graphiques côte à côte
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Répartition par zone")
            tasks_by_zone = data.count_tasks_by_zone()
            fig = visualisation.create_task_overview_chart(tasks_by_zone)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Statut des tâches")
            fig = visualisation.create_task_status_chart(tasks_by_status)
            st.plotly_chart(fig, use_container_width=True)
        
        # Afficher le graphique de priorité et le burndown chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Répartition par priorité")
            fig = visualisation.create_priority_chart(all_tasks)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Progression dans le temps")
            fig = visualisation.create_burndown_chart(all_tasks)
            st.plotly_chart(fig, use_container_width=True)
    
    # Prédiction de fin des travaux
    st.subheader("Estimation de fin des travaux")
    fig = visualisation.create_task_completion_prediction(all_tasks)
    st.pyplot(fig)
    
    # Afficher les tâches à priorité élevée
    st.markdown("<h2 class='section-header'>Tâches prioritaires</h2>", unsafe_allow_html=True)
    high_priority_tasks = all_tasks[all_tasks['priorité'] == 'Élevée']
    
    if not high_priority_tasks.empty:
        for _, task in high_priority_tasks.iterrows():
            st.markdown(utils.create_task_card(task), unsafe_allow_html=True)
    else:
        st.info("Aucune tâche à priorité élevée trouvée.")

def display_task_list():
    """Affiche la liste détaillée des tâches par zone"""
    st.markdown("<h1 class='main-header'>Liste des Travaux</h1>", unsafe_allow_html=True)
    
    # Obtenir les zones
    zones = data.get_zones()
    
    # Créer des onglets pour chaque zone
    tabs = st.tabs(zones)
    
    # Afficher les tâches pour chaque zone
    for i, zone in enumerate(zones):
        with tabs[i]:
            # Obtenir les tâches de la zone
            zone_tasks = data.get_tasks_by_zone(zone)
            
            # Afficher l'en-tête de la zone avec sa couleur
            zone_color = utils.get_color_for_zone(zone)
            st.markdown(f"<div class='zone-title' style='background-color: {zone_color};'>{zone}</div>", unsafe_allow_html=True)
            
            # Vérifier si la zone contient des tâches
            if zone_tasks.empty:
                st.info(f"Aucune tâche trouvée dans la zone {zone}. Utilisez la page 'Gérer les tâches' pour en ajouter.")
                continue
            
            # Ajouter la possibilité de filtrer par statut et priorité
            col1, col2 = st.columns(2)
            with col1:
                statut_filter = st.multiselect(
                    "Filtrer par statut",
                    options=zone_tasks['statut'].unique(),
                    default=zone_tasks['statut'].unique(),
                    key=f"statut_filter_{zone}"
                )
            
            with col2:
                priority_filter = st.multiselect(
                    "Filtrer par priorité",
                    options=zone_tasks['priorité'].unique(),
                    default=zone_tasks['priorité'].unique(),
                    key=f"priority_filter_{zone}"
                )
            
            # Appliquer les filtres
            filtered_tasks = zone_tasks[
                zone_tasks['statut'].isin(statut_filter) &
                zone_tasks['priorité'].isin(priority_filter)
            ]
            
            # Afficher les tâches filtrées
            if not filtered_tasks.empty:
                # Permettre de trier les tâches
                sort_option = st.selectbox(
                    "Trier par",
                    options=["Priorité (décroissante)", "Priorité (croissante)", "Durée (décroissante)", "Durée (croissante)"],
                    key=f"sort_{zone}"
                )
                
                # Appliquer le tri
                if sort_option == "Priorité (décroissante)":
                    priority_order = {"Élevée": 0, "Moyenne": 1, "Basse": 2, "Faible": 3}
                    filtered_tasks['priority_order'] = filtered_tasks['priorité'].map(priority_order)
                    filtered_tasks = filtered_tasks.sort_values('priority_order')
                elif sort_option == "Priorité (croissante)":
                    priority_order = {"Élevée": 0, "Moyenne": 1, "Basse": 2, "Faible": 3}
                    filtered_tasks['priority_order'] = filtered_tasks['priorité'].map(priority_order)
                    filtered_tasks = filtered_tasks.sort_values('priority_order', ascending=False)
                elif sort_option == "Durée (décroissante)":
                    filtered_tasks = filtered_tasks.sort_values('durée_estimée', ascending=False)
                elif sort_option == "Durée (croissante)":
                    filtered_tasks = filtered_tasks.sort_values('durée_estimée')
                
                # Afficher chaque tâche avec un sélecteur de statut
                for index, task in filtered_tasks.iterrows():
                    col1, col2 = st.columns([0.8, 0.2])
                    
                    with col1:
                        st.markdown(utils.create_task_card(task), unsafe_allow_html=True)
                    
                    with col2:
                        # Liste des statuts possibles
                        statuts = ["À faire", "En cours", "En attente", "Terminé"]
                        
                        # Sélecteur de statut
                        new_status = st.selectbox(
                            "Statut",
                            options=statuts,
                            index=statuts.index(task['statut']) if task['statut'] in statuts else 0,
                            key=f"status_{zone}_{index}"
                        )
                        
                        # Mettre à jour le statut si changé
                        if new_status != task['statut']:
                            if data.update_task_status(zone, task['titre'], new_status):
                                st.rerun()
            else:
                st.info(f"Aucune tâche trouvée dans la zone {zone} avec les filtres sélectionnés.")

def display_report():
    """Affiche un rapport détaillé sur l'état des travaux"""
    # Obtenir toutes les tâches
    all_tasks = data.get_all_tasks()
    
    # Générer le rapport
    utils.generate_report(all_tasks)

def manage_tasks():
    """Interface pour ajouter ou supprimer des tâches"""
    st.markdown("<h1 class='main-header'>Gestion des Tâches</h1>", unsafe_allow_html=True)
    
    # Initialiser l'onglet actif si nécessaire
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Ajouter une tâche"
    
    # Créer des onglets pour les différentes actions et définir l'onglet actif
    tab_options = ["Ajouter une tâche", "Supprimer une tâche"]
    active_tab_index = tab_options.index(st.session_state.active_tab)
    tab1, tab2 = st.tabs(tab_options)
    
    # Onglet pour ajouter une tâche
    with tab1:
        st.subheader("Ajouter une nouvelle tâche")
        
        # Formulaire pour ajouter une tâche
        with st.form(key="add_task_form"):
            # Sélectionner la zone
            zones = data.get_zones()
            
            # Utiliser la zone pré-sélectionnée si disponible
            default_zone_index = 0
            if "selected_zone_for_add" in st.session_state:
                if st.session_state.selected_zone_for_add in zones:
                    default_zone_index = zones.index(st.session_state.selected_zone_for_add)
                    # Réinitialiser pour ne pas affecter les utilisations futures
                    del st.session_state.selected_zone_for_add
                    
            selected_zone = st.selectbox("Zone", zones, index=default_zone_index)
            
            # Titre de la tâche
            task_title = st.text_input("Titre de la tâche", max_chars=100)
            
            # Priorité
            priority_options = ["Élevée", "Moyenne", "Basse", "Faible"]
            priority = st.selectbox("Priorité", priority_options, index=1)  # Par défaut: Moyenne
            
            # Choix de l'unité de temps pour la durée estimée
            time_unit = st.radio("Unité de temps", ["Jours", "Heures"], horizontal=True)
            
            # Durée estimée adaptée à l'unité choisie
            if time_unit == "Jours":
                duration = st.slider("Durée estimée (jours)", min_value=0.5, max_value=10.0, value=1.0, step=0.5,
                                   help="Durée estimée en jours de travail")
            else:  # Heures
                duration_hours = st.slider("Durée estimée (heures)", min_value=1, max_value=48, value=8, step=1,
                                         help="Durée estimée en heures de travail")
                # Convertir les heures en jours pour la base de données (1 jour = 8 heures de travail)
                duration = round(duration_hours / 8, 2)
            
            # Statut initial
            status_options = ["À faire", "En cours", "En attente", "Terminé"]
            status = st.selectbox("Statut initial", status_options, index=0)  # Par défaut: À faire
            
            # Bouton de soumission
            submit_button = st.form_submit_button(label="Ajouter la tâche")
            
        # Traiter la soumission
        if submit_button:
            if not task_title:
                st.error("Le titre de la tâche ne peut pas être vide.")
            else:
                # Stockons l'unité de temps choisie dans une variable de session
                time_unit_for_display = "jours" if time_unit == "Jours" else "heures"
                display_duration = duration if time_unit == "Jours" else duration_hours
                
                success = data.add_task(selected_zone, task_title, priority, duration, status)
                if success:
                    success_message = f"✅ Tâche '{task_title}' ajoutée avec succès dans la zone '{selected_zone}'."
                    if time_unit == "Heures":
                        success_message += f" Durée: {duration_hours} heures ({duration} jours)."
                    else:
                        success_message += f" Durée: {duration} jours."
                    
                    st.success(success_message)
                    # Afficher un bouton pour revenir à la liste des tâches
                    if st.button("Voir la liste des tâches"):
                        st.session_state.page = "Liste des travaux"
                        st.rerun()
                else:
                    st.error(f"❌ Erreur lors de l'ajout de la tâche. Une tâche avec ce titre existe peut-être déjà.")
    
    # Onglet pour supprimer une tâche
    with tab2:
        st.subheader("Supprimer une tâche existante")
        
        # Vérifier si toutes les zones sont vides
        all_tasks = data.get_all_tasks()
        if all_tasks.empty:
            st.warning("❗ Toutes les tâches ont été supprimées.")
            st.info("Utilisez l'onglet 'Ajouter une tâche' pour créer de nouvelles tâches.")
            
            # Bouton pour aller directement à l'onglet d'ajout
            if st.button("Créer une nouvelle tâche"):
                # Utiliser session_state pour changer d'onglet
                st.session_state.active_tab = "Ajouter une tâche"
                st.rerun()
            return
        
        # Sélectionner la zone
        zones = data.get_zones()
        selected_zone = st.selectbox("Zone", zones, key="delete_zone_select")
        
        # Obtenir les tâches de cette zone
        zone_tasks = data.get_tasks_by_zone(selected_zone)
        
        if not zone_tasks.empty:
            # Afficher les tâches avec des boutons de suppression
            st.write("Sélectionnez une tâche à supprimer :")
            
            for index, task in zone_tasks.iterrows():
                col1, col2 = st.columns([0.8, 0.2])
                
                with col1:
                    st.markdown(utils.create_task_card({"titre": task["titre"], "statut": task["statut"], 
                                                        "priorité": task["priorité"], "durée_estimée": task["durée_estimée"],
                                                        "zone": selected_zone}), unsafe_allow_html=True)
                
                with col2:
                    if st.button("🗑️ Supprimer", key=f"delete_{selected_zone}_{index}"):
                        if st.session_state.get(f"confirm_delete_{selected_zone}_{index}", False):
                            # Supprimer la tâche
                            success = data.delete_task(selected_zone, task["titre"])
                            if success:
                                st.success(f"✅ Tâche '{task['titre']}' supprimée avec succès.")
                                # Recharger la page
                                time.sleep(1)  # Pause d'une seconde pour montrer le message
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la suppression de la tâche.")
                        else:
                            st.session_state[f"confirm_delete_{selected_zone}_{index}"] = True
                            st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer la tâche '{task['titre']}' ? Cliquez à nouveau pour confirmer.")
        else:
            st.info(f"Aucune tâche n'existe dans la zone {selected_zone}.")
            
            # Proposer d'ajouter une tâche dans cette zone
            if st.button(f"Ajouter une tâche dans la zone {selected_zone}"):
                # Pré-sélectionner la zone dans l'onglet d'ajout
                st.session_state.selected_zone_for_add = selected_zone
                st.session_state.active_tab = "Ajouter une tâche"
                st.rerun()

if __name__ == "__main__":
    try:
        # Initialiser la page si nécessaire
        if "page" in st.session_state:
            page = st.session_state.page
            del st.session_state.page  # Réinitialiser pour la prochaine fois
        
        main()
    except Exception as e:
        st.error(f"Une erreur critique s'est produite: {e}")
        st.write("Détails de l'erreur:")
        import traceback
        st.code(traceback.format_exc()) 