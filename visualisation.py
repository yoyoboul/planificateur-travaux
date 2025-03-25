"""
Module de visualisation des travaux
"""
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

def create_task_overview_chart(tasks_by_zone):
    """Crée un graphique en barres montrant le nombre de tâches par zone"""
    fig = px.bar(
        x=list(tasks_by_zone.keys()),
        y=list(tasks_by_zone.values()),
        labels={'x': 'Zone', 'y': 'Nombre de tâches'},
        title="Aperçu des tâches par zone",
        color=list(tasks_by_zone.keys()),
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(xaxis_title="Zone", yaxis_title="Nombre de tâches")
    return fig

def create_task_status_chart(tasks_by_status):
    """Crée un graphique en camembert montrant la répartition des statuts des tâches"""
    fig = px.pie(
        values=list(tasks_by_status.values()),
        names=list(tasks_by_status.keys()),
        title="Répartition des tâches par statut",
        color=list(tasks_by_status.keys()),
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    return fig

def create_priority_chart(df):
    """Crée un graphique montrant la répartition des tâches par priorité"""
    priority_counts = df['priorité'].value_counts().reset_index()
    priority_counts.columns = ['Priorité', 'Nombre']
    
    # Définir l'ordre des priorités
    priority_order = ['Élevée', 'Moyenne', 'Basse', 'Faible']
    
    # Filtrer et trier les données
    priority_counts = priority_counts[priority_counts['Priorité'].isin(priority_order)]
    priority_counts['Priorité'] = pd.Categorical(
        priority_counts['Priorité'], 
        categories=priority_order, 
        ordered=True
    )
    priority_counts = priority_counts.sort_values('Priorité')
    
    # Définir des couleurs par priorité
    colors = {
        'Élevée': 'red',
        'Moyenne': 'orange',
        'Basse': 'blue',
        'Faible': 'green'
    }
    
    fig = px.bar(
        priority_counts,
        x='Priorité',
        y='Nombre',
        title="Répartition des tâches par priorité",
        color='Priorité',
        color_discrete_map=colors
    )
    
    return fig

def create_gantt_chart(scheduled_tasks):
    """Crée un diagramme de Gantt pour les tâches planifiées"""
    if scheduled_tasks.empty:
        return None
        
    # Prépare les données pour le diagramme de Gantt
    gantt_data = []
    for _, task in scheduled_tasks.iterrows():
        gantt_data.append(dict(
            Task=task['titre'],
            Start=task['date_début'],
            Finish=task['date_fin'],
            Resource=task['zone']
        ))
    
    df = pd.DataFrame(gantt_data)
    
    # Crée le diagramme de Gantt
    fig = ff.create_gantt(
        df, 
        colors={zone: px.colors.qualitative.Pastel[i % len(px.colors.qualitative.Pastel)] 
                for i, zone in enumerate(df['Resource'].unique())},
        index_col='Resource',
        show_colorbar=True,
        group_tasks=True,
        title="Planning des travaux"
    )
    
    fig.update_layout(
        autosize=True,
        margin=dict(l=10, r=10, t=40, b=10),
        legend_title_text="Zones"
    )
    
    return fig

def create_burndown_chart(df):
    """Crée un graphique d'avancement (burndown chart)"""
    # Calculer le nombre total de tâches
    total_tasks = len(df)
    
    # Déterminer le nombre de tâches terminées
    completed_tasks = df[df['statut'] == 'Terminé'].shape[0] if 'Terminé' in df['statut'].values else 0
    
    # Créer un échéancier sur 30 jours
    dates = [datetime.now() + timedelta(days=i) for i in range(31)]
    
    # Créer une ligne idéale de progression (du total à 0 en 30 jours)
    ideal_progress = np.linspace(total_tasks, 0, 31)
    
    # Créer une ligne de progression réelle (commence par le total moins les tâches déjà terminées)
    actual_progress = [total_tasks - completed_tasks] + [None] * 30
    
    # Créer le graphique
    fig = go.Figure()
    
    # Ajouter la ligne idéale
    fig.add_trace(go.Scatter(
        x=dates,
        y=ideal_progress,
        mode='lines',
        name='Progression idéale',
        line=dict(color='gray', dash='dash')
    ))
    
    # Ajouter la ligne réelle
    fig.add_trace(go.Scatter(
        x=dates,
        y=actual_progress,
        mode='lines+markers',
        name='Progression réelle',
        line=dict(color='blue')
    ))
    
    # Mettre à jour la mise en page
    fig.update_layout(
        title='Graphique d\'avancement',
        xaxis_title='Date',
        yaxis_title='Tâches restantes',
        legend=dict(x=0, y=1.0, bgcolor='rgba(255, 255, 255, 0.5)')
    )
    
    return fig

def create_task_completion_prediction(df):
    """Prédiction de la date d'achèvement des travaux basée sur la durée estimée"""
    # Calcul de la durée totale estimée en jours
    total_duration = df['durée_estimée'].sum()
    
    # Estimation du temps moyen par jour consacré aux travaux (supposons 3 heures par jour)
    hours_per_day = 3
    
    # Conversion de la durée en jours (8 heures de travail = 1 jour)
    estimated_days = total_duration * 8 / hours_per_day
    
    # Date d'achèvement estimée
    completion_date = datetime.now() + timedelta(days=estimated_days)
    
    # Création d'un graphique simple
    fig, ax = plt.subplots(figsize=(10, 2))
    ax.axis('off')
    
    # Affichage des informations
    ax.text(0.5, 0.7, f"Durée totale estimée: {total_duration:.1f} jours de travail",
            horizontalalignment='center', fontsize=12)
    ax.text(0.5, 0.4, f"Date d'achèvement prévue: {completion_date.strftime('%d/%m/%Y')}",
            horizontalalignment='center', fontsize=14, fontweight='bold')
    
    return fig 