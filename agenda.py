"""
Module d'agenda pour la planification des travaux
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import data
import plotly.figure_factory as ff
import plotly.express as px
import utils
import json

def get_task_color_style(task):
    """Détermine le style de couleur pour une tâche basé sur sa priorité et son statut"""
    priority_color = utils.get_color_for_priority(task['priorité'])
    status_color = utils.get_color_for_status(task['statut'])
    
    # Utiliser la couleur du statut comme couleur principale avec une bordure de la couleur de priorité
    return f"background-color: {status_color}; border-left: 3px solid {priority_color};"

def create_task_tooltip(task):
    """Crée le contenu HTML pour une infobulle détaillée"""
    zone_color = utils.get_color_for_zone(task['zone'])
    status_color = utils.get_color_for_status(task['statut'])
    priority_color = utils.get_color_for_priority(task['priorité'])
    
    tooltip_html = f"""
    <div style="padding: 10px; background-color: white; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); min-width: 200px; border-left: 5px solid {zone_color};">
        <div style="font-weight: bold; font-size: 1em; margin-bottom: 5px;">{task['titre']}</div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="color: #666;">Zone: <b style="color: {zone_color};">{task['zone']}</b></span>
            <span style="background-color: {status_color}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8em;">{task['statut']}</span>
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background-color: {priority_color}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8em;">Priorité: {task['priorité']}</span>
        </div>
        <div style="font-size: 0.85em; color: #444; margin-top: 5px;">
            Durée: {utils.format_duration(task['durée_estimée'])}
        </div>
        <div style="font-size: 0.85em; color: #444; margin-top: 5px;">
            Du {task['date_début'].strftime('%d/%m/%Y')} au {task['date_fin'].strftime('%d/%m/%Y')}
        </div>
    </div>
    """
    return tooltip_html

def create_tooltip_text(task):
    """Crée un texte formaté pour l'attribut title HTML"""
    tooltip_text = f"""
{task['titre']}
Zone: {task['zone']}
{task['statut']}
Priorité: {task['priorité']}
Durée: {utils.format_duration(task['durée_estimée'])}
Du {task['date_début'].strftime('%d/%m/%Y')} au {task['date_fin'].strftime('%d/%m/%Y')}
    """.strip()
    
    return tooltip_text

def display_daily_view(selected_date):
    """Affiche une vue détaillée d'une journée"""
    st.write(f"## {selected_date.strftime('%A %d %B %Y')}")
    
    # Obtenir les tâches planifiées
    scheduled_tasks = data.get_scheduled_tasks()
    
    if scheduled_tasks.empty:
        st.info("Aucune tâche n'est planifiée pour cette journée.")
        return
    
    # Filtrer les tâches pour cette journée
    day_tasks = []
    for _, task in scheduled_tasks.iterrows():
        if task["date_début"].date() <= selected_date.date() <= task["date_fin"].date():
            day_tasks.append(task)
    
    if not day_tasks:
        st.info(f"Aucune tâche planifiée pour le {selected_date.strftime('%d/%m/%Y')}.")
        return
    
    # Afficher les tâches du jour sous forme de cartes
    st.write("### Tâches du jour")
    
    for task in day_tasks:
        # Créer une carte pour chaque tâche
        st.markdown(utils.create_task_card(task), unsafe_allow_html=True)
        
        # Ajouter des boutons d'action sous chaque carte
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            # Bouton pour modifier le statut
            statuts = ["À faire", "En cours", "En attente", "Terminé"]
            new_status = st.selectbox(
                "Statut",
                options=statuts,
                index=statuts.index(task['statut']) if task['statut'] in statuts else 0,
                key=f"status_daily_{task['zone']}_{task['titre']}"
            )
            
            # Mettre à jour le statut si changé
            if new_status != task['statut']:
                if data.update_task_status(task['zone'], task['titre'], new_status):
                    st.rerun()
        
        with col2:
            # Bouton pour déplanifier la tâche
            if st.button("🗑️ Déplanifier", key=f"unschedule_daily_{task['zone']}_{task['titre']}"):
                confirm_key = f"confirm_unschedule_daily_{task['zone']}_{task['titre']}"
                if st.session_state.get(confirm_key, False):
                    success = data.unschedule_task(task['zone'], task['titre'])
                    if success:
                        st.success(f"Tâche '{task['titre']}' déplanifiée avec succès.")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la déplanification de la tâche.")
                else:
                    st.session_state[confirm_key] = True
                    st.warning(f"⚠️ Êtes-vous sûr de vouloir déplanifier la tâche '{task['titre']}'? Cliquez à nouveau pour confirmer.")
        
        st.markdown("---")

def display_weekly_view(start_date):
    """Affiche une vue de la semaine"""
    # Déterminer le premier et le dernier jour de la semaine
    # Le premier jour est lundi (weekday=0) et le dernier jour est dimanche (weekday=6)
    current_weekday = start_date.weekday()
    first_day = start_date - timedelta(days=current_weekday)
    last_day = first_day + timedelta(days=6)
    
    st.write(f"## Semaine du {first_day.strftime('%d/%m/%Y')} au {last_day.strftime('%d/%m/%Y')}")
    
    # Obtenir les tâches planifiées
    scheduled_tasks = data.get_scheduled_tasks()
    
    # Créer un dictionnaire pour stocker les tâches par jour
    week_tasks = {(first_day + timedelta(days=i)).date(): [] for i in range(7)}
    
    # Remplir le dictionnaire avec les tâches
    if not scheduled_tasks.empty:
        for _, task in scheduled_tasks.iterrows():
            for i in range(7):
                day = (first_day + timedelta(days=i)).date()
                if task["date_début"].date() <= day <= task["date_fin"].date():
                    week_tasks[day].append(task)
    
    # Afficher les jours de la semaine
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    
    # Créer une grille pour afficher la semaine
    cols = st.columns(7)
    
    # Afficher les en-têtes des jours
    for i, day_name in enumerate(days):
        day = first_day + timedelta(days=i)
        is_today = day.date() == datetime.now().date()
        
        # Highlight du jour actuel
        day_style = "font-weight: bold; color: #1E88E5;" if is_today else ""
        
        cols[i].markdown(f"<div style='{day_style}'>{day_name}<br>{day.day}/{day.month}</div>", unsafe_allow_html=True)
    
    # Afficher les tâches de la semaine
    for row in range(6):  # Maximum 6 tâches par jour pour la lisibilité
        week_cols = st.columns(7)
        
        for i in range(7):
            day = (first_day + timedelta(days=i)).date()
            day_tasks = week_tasks[day]
            
            if row < len(day_tasks):
                task = day_tasks[row]
                
                # Créer le style basé sur la priorité et le statut
                task_style = get_task_color_style(task)
                
                # Créer un texte pour l'infobulle native
                tooltip_text = create_tooltip_text(task)
                tooltip_text = tooltip_text.replace('"', '&quot;')  # Échapper les guillemets
                
                # Ajouter des icônes pour le statut
                status_icon = "✅" if task['statut'] == "Terminé" else "🔄" if task['statut'] == "En cours" else "⏱️" if task['statut'] == "En attente" else "📋"
                
                # Créer une carte minimaliste pour la tâche avec attribut title HTML et icônes
                task_html = f"""
                <div class="task-card" 
                     style="{task_style} padding: 5px; margin: 2px 0; border-radius: 4px; color: white; font-size: 0.8em;"
                     title="{tooltip_text}">
                    {status_icon} {task['titre'][:12]}{"..." if len(task['titre']) > 12 else ""}
                </div>
                """
                week_cols[i].markdown(task_html, unsafe_allow_html=True)
                
                # Ajouter un bouton pour voir les détails de la tâche
                if week_cols[i].button("📋", key=f"details_{day}_{row}"):
                    st.session_state.selected_date = datetime.combine(day, datetime.min.time())
                    st.session_state.calendar_view = "daily"
                    st.rerun()
            
            elif row == 0 and not day_tasks:
                week_cols[i].markdown("<div style='text-align: center; color: #888; font-size: 0.8em;'>Aucune tâche</div>", unsafe_allow_html=True)

def display_calendar(start_date=None):
    """Affiche un calendrier interactif pour la planification des tâches"""
    if start_date is None:
        start_date = datetime.now()
    
    # Initialiser la vue du calendrier si nécessaire
    if "calendar_view" not in st.session_state:
        st.session_state.calendar_view = "monthly"
    
    # Navigation entre les différentes vues
    col_view1, col_view2, col_view3, col_today = st.columns([1, 1, 1, 1])
    
    with col_view1:
        if st.button("📅 Vue mensuelle", key="btn_monthly"):
            st.session_state.calendar_view = "monthly"
            st.rerun()
    
    with col_view2:
        if st.button("📆 Vue hebdomadaire", key="btn_weekly"):
            st.session_state.calendar_view = "weekly"
            st.rerun()
    
    with col_view3:
        if st.button("📆 Vue journalière", key="btn_daily"):
            st.session_state.calendar_view = "daily"
            st.rerun()
    
    with col_today:
        # Bouton pour revenir à aujourd'hui
        if st.button("📍 Aujourd'hui", key="btn_today"):
            st.session_state.calendar_date = datetime.now()
            st.rerun()
    
    # Afficher la vue appropriée
    if st.session_state.calendar_view == "daily":
        display_daily_view(st.session_state.calendar_date)
        
        # Ajouter des boutons pour naviguer entre les jours
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Jour précédent"):
                st.session_state.calendar_date = st.session_state.calendar_date - timedelta(days=1)
                st.rerun()
        
        with col2:
            if st.button("Jour suivant ➡️"):
                st.session_state.calendar_date = st.session_state.calendar_date + timedelta(days=1)
                st.rerun()
                
    elif st.session_state.calendar_view == "weekly":
        display_weekly_view(st.session_state.calendar_date)
        
        # Ajouter des boutons pour naviguer entre les semaines
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Semaine précédente"):
                st.session_state.calendar_date = st.session_state.calendar_date - timedelta(days=7)
                st.rerun()
        
        with col2:
            if st.button("Semaine suivante ➡️"):
                st.session_state.calendar_date = st.session_state.calendar_date + timedelta(days=7)
                st.rerun()
                
    else:  # monthly view (default)
        # Calculer le début et la fin du mois
        first_day = start_date.replace(day=1)
        
        # Déterminer le dernier jour du mois
        if first_day.month == 12:
            last_day = first_day.replace(year=first_day.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = first_day.replace(month=first_day.month + 1, day=1) - timedelta(days=1)
        
        # Créer une liste de dates pour le mois
        month_days = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
        
        # Créer une grille pour l'affichage du calendrier
        st.write(f"## {start_date.strftime('%B %Y')}")
        
        # Navigation entre les mois
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⬅️ Mois précédent"):
                if start_date.month == 1:
                    new_date = start_date.replace(year=start_date.year - 1, month=12)
                else:
                    new_date = start_date.replace(month=start_date.month - 1)
                st.session_state.calendar_date = new_date
                st.rerun()
        
        with col2:
            if st.button("Mois suivant ➡️"):
                if start_date.month == 12:
                    new_date = start_date.replace(year=start_date.year + 1, month=1)
                else:
                    new_date = start_date.replace(month=start_date.month + 1)
                st.session_state.calendar_date = new_date
                st.rerun()
        
        # Obtenir les tâches planifiées
        scheduled_tasks = data.get_scheduled_tasks()
        
        # Créer la grille du calendrier
        days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        
        # Trouver le jour de la semaine du premier jour du mois
        first_weekday = first_day.weekday()
        
        # Créer la grille complète avec les jours précédents du mois précédent
        all_days = []
        
        # Jours du mois précédent
        if first_weekday > 0:
            for i in range(first_weekday, 0, -1):
                prev_date = first_day - timedelta(days=i)
                all_days.append({"date": prev_date, "current_month": False})
        
        # Jours du mois actuel
        for day in month_days:
            all_days.append({"date": day, "current_month": True})
        
        # Calculer le nombre de jours nécessaires pour compléter la dernière semaine
        remaining_days = 7 - (len(all_days) % 7)
        if remaining_days < 7:
            for i in range(1, remaining_days + 1):
                next_date = last_day + timedelta(days=i)
                all_days.append({"date": next_date, "current_month": False})
        
        # Afficher l'en-tête des jours de la semaine
        st.write("### Calendrier")
        cols = st.columns(7)
        for i, day in enumerate(days):
            cols[i].write(f"**{day}**")
        
        # Afficher les jours dans une grille
        rows = [all_days[i:i+7] for i in range(0, len(all_days), 7)]
        
        for row in rows:
            cols = st.columns(7)
            for i, day_info in enumerate(row):
                day = day_info["date"]
                is_current_month = day_info["current_month"]
                is_today = day.date() == datetime.now().date()
                
                # Formater la couleur des jours
                date_style = "color: gray;" if not is_current_month else ""
                if is_today:
                    date_style += "font-weight: bold; background-color: #e8f0fe; border-radius: 50%; display: inline-block; width: 25px; height: 25px; text-align: center; line-height: 25px;"
                
                # Vérifier s'il y a des tâches planifiées pour cette date
                day_tasks = []
                if not scheduled_tasks.empty:
                    for _, task in scheduled_tasks.iterrows():
                        if task["date_début"].date() <= day.date() <= task["date_fin"].date():
                            day_tasks.append(task)
                
                # Afficher le jour avec son style
                cols[i].markdown(f"<div style='{date_style}'>{day.day}</div>", unsafe_allow_html=True)
                
                # S'il y a des tâches ce jour-là, les afficher avec un style basé sur le statut/priorité
                if day_tasks:
                    for task in day_tasks[:3]:  # Limiter à 3 tâches visibles par jour
                        # Créer le style basé sur le statut et la priorité
                        task_style = get_task_color_style(task)
                        
                        # Créer un texte pour l'infobulle native
                        tooltip_text = create_tooltip_text(task)
                        tooltip_text = tooltip_text.replace('"', '&quot;')  # Échapper les guillemets
                        
                        # Ajouter des icônes pour le statut
                        status_icon = "✅" if task['statut'] == "Terminé" else "🔄" if task['statut'] == "En cours" else "⏱️" if task['statut'] == "En attente" else "📋"
                        
                        # Créer la div de la tâche avec l'attribut title HTML et icônes
                        task_html = f"""
                        <div style="{task_style} padding: 3px; margin: 2px 0; border-radius: 3px; color: white; font-size: 0.7em; cursor: pointer;"
                             title="{tooltip_text}">
                            {status_icon} {task['titre'][:10]}{"..." if len(task['titre']) > 10 else ""}
                        </div>
                        """
                        cols[i].markdown(task_html, unsafe_allow_html=True)
                    
                    if len(day_tasks) > 3:
                        cols[i].markdown(f"<div style='font-size: 0.7em; text-align: center;'>+{len(day_tasks) - 3} autres</div>", unsafe_allow_html=True)
                
                # Permettre d'ajouter une tâche en cliquant sur un jour
                if is_current_month:
                    # Ajouter un bouton pour voir les détails du jour
                    if cols[i].button("📋", key=f"view_day_{day.day}"):
                        st.session_state.selected_date = day
                        st.session_state.calendar_view = "daily"
                        st.rerun()
                    
                    # Ajouter une tâche
                    if cols[i].button("➕", key=f"add_task_{day.day}"):
                        st.session_state.selected_date = day
                        st.session_state.show_task_scheduler = True
                        st.rerun()
    
    # Mettre à jour la note explicative
    st.markdown("""
    > **Note:** Les infobulles simples apparaissent maintenant au survol des tâches.
    > Pour des détails plus complets, cliquez sur une tâche pour accéder à la vue journalière.
    """)
    
    return None

def schedule_task_ui():
    """Interface pour planifier une tâche"""
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.now()
    
    selected_date = st.session_state.selected_date
    
    st.write(f"## Planifier une tâche pour le {selected_date.strftime('%d/%m/%Y')}")
    
    # Obtenir toutes les zones
    zones = data.get_zones()
    
    # Sélectionner une zone
    selected_zone = st.selectbox("Sélectionner une zone", zones)
    
    # Obtenir toutes les tâches de cette zone
    zone_tasks = data.get_tasks_by_zone(selected_zone)
    
    # Sélectionner une tâche
    if not zone_tasks.empty:
        task_titles = zone_tasks["titre"].tolist()
        selected_task = st.selectbox("Sélectionner une tâche", task_titles)
        
        # Options de durée
        default_duration = zone_tasks[zone_tasks["titre"] == selected_task]["durée_estimée"].values[0]
        st.write(f"Durée estimée par défaut: {default_duration} jours")
        
        # Permettre à l'utilisateur de modifier la durée estimée
        custom_duration = st.slider(
            "Modifier la durée estimée (en jours)",
            min_value=0.5,
            max_value=10.0,
            value=default_duration,
            step=0.5,
            key=f"duration_slider_{selected_task}"
        )
        
        # Bouton pour planifier la tâche
        if st.button("Planifier cette tâche"):
            # Passer la durée personnalisée à la fonction de planification
            success = data.schedule_task(selected_zone, selected_task, selected_date, custom_duration)
            if success:
                st.success(f"Tâche '{selected_task}' planifiée pour le {selected_date.strftime('%d/%m/%Y')} avec une durée de {custom_duration} jours")
                # Retourner à l'affichage du calendrier
                st.session_state.show_task_scheduler = False
                st.rerun()
            else:
                st.error("Erreur lors de la planification de la tâche")
    else:
        st.write("Aucune tâche disponible dans cette zone")
    
    # Bouton pour annuler
    if st.button("Annuler"):
        st.session_state.show_task_scheduler = False
        st.rerun()

def display_gantt_chart():
    """Affiche un diagramme de Gantt des tâches planifiées"""
    # Obtenir les tâches planifiées
    scheduled_tasks = data.get_scheduled_tasks()
    
    if scheduled_tasks.empty:
        st.info("Aucune tâche n'a encore été planifiée. Utilisez le calendrier pour planifier des tâches.")
        return
    
    # Préparer les données pour le diagramme de Gantt
    gantt_data = []
    for _, task in scheduled_tasks.iterrows():
        gantt_data.append(dict(
            Task=task['titre'],
            Start=task['date_début'],
            Finish=task['date_fin'],
            Resource=task['zone']
        ))
    
    df = pd.DataFrame(gantt_data)
    
    # Créer le diagramme de Gantt
    fig = ff.create_gantt(
        df, 
        colors={zone: utils.get_color_for_zone(zone) for zone in df['Resource'].unique()},
        index_col='Resource',
        show_colorbar=True,
        group_tasks=True,
        title="Planning des travaux"
    )
    
    fig.update_layout(
        autosize=True,
        height=600,
        margin=dict(l=10, r=10, t=40, b=10),
        legend_title_text="Zones"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def manage_scheduled_tasks():
    """Interface pour gérer les tâches planifiées (visualiser, modifier, déplanifier)"""
    st.write("## Gestion des tâches planifiées")
    
    # Obtenir les tâches planifiées
    scheduled_tasks = data.get_scheduled_tasks()
    
    if scheduled_tasks.empty:
        st.info("Aucune tâche n'est actuellement planifiée. Utilisez le calendrier pour planifier des tâches.")
        return
    
    # Ajouter des colonnes pour faciliter l'affichage
    scheduled_tasks["Date de début"] = scheduled_tasks["date_début"].dt.strftime("%d/%m/%Y")
    scheduled_tasks["Date de fin"] = scheduled_tasks["date_fin"].dt.strftime("%d/%m/%Y")
    scheduled_tasks["Durée (jours)"] = [(task["date_fin"] - task["date_début"]).days + 1 for _, task in scheduled_tasks.iterrows()]
    
    # Afficher les tâches planifiées dans un tableau
    st.write("### Tâches planifiées")
    
    # Créer un tableau plus lisible avec les colonnes importantes
    display_df = scheduled_tasks[["zone", "titre", "Date de début", "Date de fin", "Durée (jours)", "priorité", "statut"]]
    display_df.columns = ["Zone", "Tâche", "Début", "Fin", "Durée", "Priorité", "Statut"]
    
    # Grouper par zone pour une meilleure lisibilité
    st.write("Sélectionnez une zone pour voir ses tâches planifiées :")
    zones = scheduled_tasks["zone"].unique()
    selected_zone = st.selectbox("Zone", zones, key="scheduled_zone_select")
    
    # Filtrer par zone sélectionnée
    zone_scheduled_tasks = scheduled_tasks[scheduled_tasks["zone"] == selected_zone]
    
    # Afficher les tâches de cette zone avec des boutons pour déplanifier
    for _, task in zone_scheduled_tasks.iterrows():
        col1, col2 = st.columns([0.7, 0.3])
        
        with col1:
            task_info = f"""
            **{task['titre']}**  
            *{task['statut']} - Priorité {task['priorité']}*  
            📅 Du {task['Date de début']} au {task['Date de fin']} ({task['Durée (jours)']} jours)
            """
            st.markdown(task_info)
        
        with col2:
            # Bouton pour déplanifier la tâche
            if st.button("🗑️ Déplanifier", key=f"unschedule_{selected_zone}_{task['titre']}"):
                # Vérifier si l'utilisateur a déjà confirmé
                confirm_key = f"confirm_unschedule_{selected_zone}_{task['titre']}"
                if st.session_state.get(confirm_key, False):
                    # Déplanifier la tâche
                    success = data.unschedule_task(selected_zone, task["titre"])
                    if success:
                        st.success(f"Tâche '{task['titre']}' déplanifiée avec succès.")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la déplanification de la tâche.")
                else:
                    # Demander confirmation
                    st.session_state[confirm_key] = True
                    st.warning(f"⚠️ Êtes-vous sûr de vouloir déplanifier la tâche '{task['titre']}'? Cliquez à nouveau pour confirmer.")
        
        # Séparateur entre les tâches
        st.markdown("---")

def display_agenda():
    """Affiche l'interface principale de l'agenda"""
    st.title("Agenda des Travaux")
    
    # Initialiser les variables de session si nécessaire
    if "calendar_date" not in st.session_state:
        st.session_state.calendar_date = datetime.now()
    if "show_task_scheduler" not in st.session_state:
        st.session_state.show_task_scheduler = False
    
    # Onglets pour différentes vues
    tab1, tab2, tab3 = st.tabs(["Calendrier", "Diagramme de Gantt", "Gestion des tâches planifiées"])
    
    with tab1:
        if st.session_state.show_task_scheduler:
            schedule_task_ui()
        else:
            display_calendar(st.session_state.calendar_date)
    
    with tab2:
        display_gantt_chart()
    
    with tab3:
        manage_scheduled_tasks() 