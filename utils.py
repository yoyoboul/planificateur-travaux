"""
Module d'utilitaires pour l'application de planification des travaux
"""
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import random

# Configuration des couleurs par zone
ZONE_COLORS = {
    "Palier": "#4CAF50",  # Vert
    "Cuisine/Séjour": "#2196F3",  # Bleu
    "Escalier": "#9C27B0",  # Violet
    "Cuisine": "#FF9800"   # Orange
}

# Configuration des couleurs par priorité
PRIORITY_COLORS = {
    "Élevée": "#F44336",  # Rouge
    "Moyenne": "#FF9800",  # Orange
    "Basse": "#2196F3",    # Bleu
    "Faible": "#4CAF50"    # Vert
}

# Configuration des couleurs par statut
STATUS_COLORS = {
    "À faire": "#F44336",       # Rouge
    "En cours": "#FF9800",      # Orange
    "Terminé": "#4CAF50",       # Vert
    "En attente": "#9E9E9E"     # Gris
}

def format_duration(days):
    """Formate la durée en jours ou heures pour l'affichage"""
    if days >= 1:
        return f"{days:.1f} jour{'s' if days > 1 else ''}"
    else:
        hours = days * 8  # Conversion en heures (8 heures = 1 journée de travail)
        return f"{hours:.1f} heure{'s' if hours > 1 else ''}"

def get_color_for_zone(zone):
    """Retourne la couleur associée à une zone"""
    return ZONE_COLORS.get(zone, "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)]))

def get_color_for_priority(priority):
    """Retourne la couleur associée à une priorité"""
    return PRIORITY_COLORS.get(priority, "#9E9E9E")

def get_color_for_status(status):
    """Retourne la couleur associée à un statut"""
    return STATUS_COLORS.get(status, "#9E9E9E")

def create_task_card(task):
    """Crée une carte pour afficher une tâche"""
    zone = task.get('zone', '')
    title = task.get('titre', '')
    status = task.get('statut', 'À faire')
    priority = task.get('priorité', 'Moyenne')
    duration = task.get('durée_estimée', 0)
    
    # Obtenir les couleurs
    zone_color = get_color_for_zone(zone)
    status_color = get_color_for_status(status)
    priority_color = get_color_for_priority(priority)
    
    # Créer la carte
    card_html = f"""
    <div style="border-left: 5px solid {zone_color}; padding: 10px; margin-bottom: 10px; background-color: white; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: bold; font-size: 1.1em;">{title}</span>
            <span style="background-color: {status_color}; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.8em;">{status}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.9em; color: #666;">
            <span>Zone: <b>{zone}</b></span>
            <span style="background-color: {priority_color}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8em;">Priorité: {priority}</span>
        </div>
        <div style="font-size: 0.85em; color: #888; margin-top: 5px;">
            Durée estimée: {format_duration(duration)}
        </div>
    </div>
    """
    return card_html

def generate_report(df):
    """Génère un rapport de l'état des travaux"""
    st.title("Rapport d'avancement des travaux")
    
    # Statistiques globales
    total_tasks = len(df)
    completed_tasks = df[df['statut'] == 'Terminé'].shape[0] if 'Terminé' in df['statut'].values else 0
    in_progress_tasks = df[df['statut'] == 'En cours'].shape[0] if 'En cours' in df['statut'].values else 0
    waiting_tasks = df[df['statut'] == 'En attente'].shape[0] if 'En attente' in df['statut'].values else 0
    todo_tasks = df[df['statut'] == 'À faire'].shape[0] if 'À faire' in df['statut'].values else 0
    
    completion_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    
    # Afficher les statistiques globales
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total des tâches", total_tasks)
    col2.metric("Tâches terminées", completed_tasks)
    col3.metric("Tâches en cours", in_progress_tasks)
    col4.metric("Tâches en attente", waiting_tasks)
    
    st.progress(completion_percentage / 100)
    st.write(f"**Progression globale: {completion_percentage:.1f}%**")
    
    # Répartition des tâches par zone
    st.subheader("Répartition des tâches par zone")
    zone_counts = df['zone'].value_counts().reset_index()
    zone_counts.columns = ['Zone', 'Nombre']
    
    fig = px.bar(
        zone_counts,
        x='Zone',
        y='Nombre',
        color='Zone',
        color_discrete_map={zone: get_color_for_zone(zone) for zone in zone_counts['Zone']}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Répartition des tâches par statut
    st.subheader("Répartition des tâches par statut")
    status_counts = df['statut'].value_counts().reset_index()
    status_counts.columns = ['Statut', 'Nombre']
    
    fig = px.pie(
        status_counts,
        values='Nombre',
        names='Statut',
        color='Statut',
        color_discrete_map={status: get_color_for_status(status) for status in status_counts['Statut']}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Répartition des tâches par priorité
    st.subheader("Répartition des tâches par priorité")
    priority_counts = df['priorité'].value_counts().reset_index()
    priority_counts.columns = ['Priorité', 'Nombre']
    
    fig = px.pie(
        priority_counts,
        values='Nombre',
        names='Priorité',
        color='Priorité',
        color_discrete_map={priority: get_color_for_priority(priority) for priority in priority_counts['Priorité']}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Tâches à priorité élevée non terminées
    st.subheader("Tâches prioritaires à faire")
    high_priority_tasks = df[(df['priorité'] == 'Élevée') & (df['statut'] != 'Terminé')]
    
    if not high_priority_tasks.empty:
        for _, task in high_priority_tasks.iterrows():
            st.markdown(create_task_card(task), unsafe_allow_html=True)
    else:
        st.info("Aucune tâche prioritaire en attente.")
    
    # Estimation du temps restant
    st.subheader("Estimation du temps restant")
    remaining_tasks = df[df['statut'] != 'Terminé']
    total_remaining_duration = remaining_tasks['durée_estimée'].sum()
    
    # Estimation avec un rythme de 3 heures par jour
    hours_per_day = 3
    estimated_days = total_remaining_duration * 8 / hours_per_day
    completion_date = datetime.now() + timedelta(days=estimated_days)
    
    st.write(f"**Durée totale estimée des tâches restantes:** {format_duration(total_remaining_duration)}")
    st.write(f"**Date d'achèvement prévue:** {completion_date.strftime('%d/%m/%Y')}")
    
    # Prochaines tâches recommandées
    st.subheader("Tâches recommandées pour la semaine")
    # Trier par priorité et durée
    recommended_tasks = df[df['statut'] == 'À faire'].sort_values(by=['priorité', 'durée_estimée'], 
                                                                ascending=[True, True])
    
    if not recommended_tasks.empty:
        for _, task in recommended_tasks.head(5).iterrows():
            st.markdown(create_task_card(task), unsafe_allow_html=True)
    else:
        st.info("Toutes les tâches sont terminées ou en cours.")
    
    return None 