"""
Application Streamlit - Comparateur de Villes Françaises
Projet noté BUT SD2 VCOD - Programmation Web

Auteurs: Groupe Streamlit
Date: Mars 2026
Description: Interface de comparaison de 2 villes françaises (> 20 000 hab.)
             avec indicateurs Emploi, Logement, Météo et Cartographie
"""

import streamlit
import pandas
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

# ============================================================================
# 1. CONFIGURATION GLOBALE DE L'APPLICATION
# ============================================================================

streamlit.set_page_config(
    page_title="Comparateur de Villes Françaises | Projet Web",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# 2. FONCTIONS DE CHARGEMENT DES DONNÉES
# ============================================================================

@streamlit.cache_data
def charger_donnees():
    """
    Charge et fusionne les données INSEE et géographiques.
    Filtre les communes de plus de 20 000 habitants (contrainte projet).
    
    Returns:
        pandas.DataFrame: Données complètes triées par nom de commune
    """
    # A. Chargement de la base INSEE (indicateurs socio-économiques)
    data_insee = pandas.read_csv("base_cc_comparateur.csv", sep=";", low_memory=False)
    
    # B. Chargement du fichier géographique (coordonnées GPS)
    data_gps = pandas.read_csv("20230823-communes-departement-region.csv", sep=",")
    
    # C. Normalisation des codes communes en format 5 caractères
    data_gps["code_commune_INSEE"] = data_gps["code_commune_INSEE"].astype(str).str.zfill(5)
    data_insee["CODGEO"] = data_insee["CODGEO"].astype(str).str.zfill(5)

    # D. Filtrage : communes > 20 000 habitants (critère sujet)
    data_20k = data_insee.query("P22_POP > 20000")
    
    # E. Fusion des données INSEE et géographiques
    donnees_completes = pandas.merge(
        data_20k, data_gps, 
        left_on="CODGEO", 
        right_on="code_commune_INSEE", 
        how="inner"
    )
    
    # F. Suppression des doublons éventuels
    donnees_completes = donnees_completes.drop_duplicates(subset=['CODGEO'])
    
    return donnees_completes.sort_values(by="nom_commune_complet")


@streamlit.cache_data(ttl=3600)  # Cache de 1h pour les données météo
def obtenir_meteo(ville_nom, latitude, longitude):
    """
    Récupère les prévisions météo via Open-Meteo API (gratuite, sans clé).
    
    Args:
        ville_nom: Nom de la ville
        latitude: Latitude GPS
        longitude: Longitude GPS
        
    Returns:
        dict: Données météo ou None en cas d'erreur
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone": "Europe/Paris",
            "forecast_days": 5
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        streamlit.warning(f"Impossible de récupérer la météo pour {ville_nom}: {e}")
        return None


def code_meteo_vers_emoji(code):
    """Convertit un code météo WMO en emoji."""
    codes_emojis = {
        0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
        45: "🌫️", 48: "🌫️",
        51: "🌦️", 53: "🌧️", 55: "🌧️",
        61: "🌧️", 63: "🌧️", 65: "🌧️",
        71: "🌨️", 73: "🌨️", 75: "🌨️",
        80: "🌦️", 81: "🌧️", 82: "⛈️",
        95: "⛈️", 96: "⛈️", 99: "⛈️"
    }
    return codes_emojis.get(code, "🌡️")


# ============================================================================
# 3. CHARGEMENT DES DONNÉES PRINCIPALES
# ============================================================================

villes_data = charger_donnees()
liste_villes = list(villes_data["nom_commune_complet"])

# ============================================================================
# 4. SIDEBAR - SÉLECTION DES VILLES
# ============================================================================

with streamlit.sidebar:
    streamlit.title("🏙️ Comparateur de Villes")
    streamlit.markdown("---")
    streamlit.header("Sélection des villes")
    
    # Villes par défaut : Niort et Lorient
    default_A = liste_villes.index("Niort") if "Niort" in liste_villes else 0
    default_B = liste_villes.index("Lorient") if "Lorient" in liste_villes else (1 if len(liste_villes) > 1 else 0)
    
    ville_A = streamlit.selectbox(
        "🔵 Ville A", 
        liste_villes, 
        index=default_A,
        key="ville_a"
    )
    
    ville_B = streamlit.selectbox(
        "🟠 Ville B", 
        liste_villes, 
        index=default_B,
        key="ville_b"
    )
    
    streamlit.markdown("---")
    streamlit.info(f" {len(liste_villes)} villes disponibles\n(> 20 000 habitants)")
    streamlit.caption("Projet BUT SD2 VCOD - Mars 2026")

# Extraction des données pour les villes sélectionnées
temp_A = villes_data.query("nom_commune_complet == @ville_A")
temp_B = villes_data.query("nom_commune_complet == @ville_B")

# ============================================================================
# 5. CRÉATION DES ONGLETS
# ============================================================================

onglet1, onglet2, onglet3, onglet4, onglet5, onglet6, onglet7, onglet8 = streamlit.tabs([
    "📍 Généralités & Carte",
    "💼 Emploi",
    "🏠 Logement",
    "🌦️ Météo",
    "🎓 Formation",
    "🏅 Sports",
    "🎭 Culture",
    "🧭 Tourisme"
])

# ============================================================================
# ONGLET 1 : GÉNÉRALITÉS & CARTOGRAPHIE
# ============================================================================

with onglet1:
    streamlit.header("Informations Générales", divider="blue")
    
    # Métriques principales en colonnes
    col1, col2 = streamlit.columns(2)
    
    with col1:
        streamlit.subheader(f"🔵 {ville_A}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Population 2022", f"{int(temp_A['P22_POP'].values[0]):,}".replace(",", " "))
        m2.metric("Superficie (km²)", f"{int(temp_A['SUPERF'].values[0]):,}".replace(",", " "))
        densite_A = int(temp_A['P22_POP'].values[0] / temp_A['SUPERF'].values[0])
        m3.metric("Densité (hab/km²)", f"{densite_A:,}".replace(",", " "))
        
        # Métriques supplémentaires
        m4, m5 = streamlit.columns(2)
        m4.metric("Ménages", f"{int(temp_A['P22_MEN'].values[0]):,}".replace(",", " "))
        m5.metric("Revenu médian", f"{int(temp_A['MED21'].values[0]):,} €".replace(",", " "))
        
    with col2:
        streamlit.subheader(f"🟠 {ville_B}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Population 2022", f"{int(temp_B['P22_POP'].values[0]):,}".replace(",", " "))
        m2.metric("Superficie (km²)", f"{int(temp_B['SUPERF'].values[0]):,}".replace(",", " "))
        densite_B = int(temp_B['P22_POP'].values[0] / temp_B['SUPERF'].values[0])
        m3.metric("Densité (hab/km²)", f"{densite_B:,}".replace(",", " "))
        
        # Métriques supplémentaires
        m4, m5 = streamlit.columns(2)
        m4.metric("Ménages", f"{int(temp_B['P22_MEN'].values[0]):,}".replace(",", " "))
        m5.metric("Revenu médian", f"{int(temp_B['MED21'].values[0]):,} €".replace(",", " "))
    
    streamlit.divider()
    
    # Cartographie interactive
    streamlit.subheader("🗺️ Localisation géographique")
    
    villes_comparees = pandas.concat([temp_A, temp_B])
    
    fig_carte = px.scatter_mapbox(
        villes_comparees,
        lat="latitude",
        lon="longitude",
        hover_name="nom_commune_complet",
        hover_data={
            "latitude": False,
            "longitude": False,
            "P22_POP": ":,",
            "nom_departement": True
        },
        size="P22_POP",
        color="nom_commune_complet",
        color_discrete_map={ville_A: "#1f77b4", ville_B: "#ff7f0e"},
        zoom=5.5,
        height=500,
        mapbox_style="carto-positron"
    )
    
    fig_carte.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    streamlit.plotly_chart(fig_carte, use_container_width=True)

# ============================================================================
# ONGLET 2 : EMPLOI
# ============================================================================

with onglet2:
    streamlit.header("Indicateurs Emploi", divider="blue")
    
    # Calculs des indicateurs emploi
    pop15_64_A = temp_A['P22_POP1564'].values[0]
    actifs_A = temp_A['P22_ACT1564'].values[0]
    chomeurs_A = temp_A['P22_CHOM1564'].values[0]
    emplois_A = temp_A['P22_EMPLT'].values[0]
    emplois_sal_A = temp_A['P22_EMPLT_SAL'].values[0]
    
    pop15_64_B = temp_B['P22_POP1564'].values[0]
    actifs_B = temp_B['P22_ACT1564'].values[0]
    chomeurs_B = temp_B['P22_CHOM1564'].values[0]
    emplois_B = temp_B['P22_EMPLT'].values[0]
    emplois_sal_B = temp_B['P22_EMPLT_SAL'].values[0]
    
    # Taux de chômage
    taux_chom_A = (chomeurs_A / actifs_A * 100) if actifs_A > 0 else 0
    taux_chom_B = (chomeurs_B / actifs_B * 100) if actifs_B > 0 else 0
    
    # Taux d'activité
    taux_act_A = (actifs_A / pop15_64_A * 100) if pop15_64_A > 0 else 0
    taux_act_B = (actifs_B / pop15_64_B * 100) if pop15_64_B > 0 else 0
    
    # Affichage des métriques
    col1, col2 = streamlit.columns(2)
    
    with col1:
        streamlit.subheader(f"🔵 {ville_A}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Taux d'activité", f"{taux_act_A:.1f}%")
        m2.metric("Taux de chômage", f"{taux_chom_A:.1f}%")
        m3.metric("Emplois totaux", f"{int(emplois_A):,}".replace(",", " "))
    
    with col2:
        streamlit.subheader(f"🟠 {ville_B}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Taux d'activité", f"{taux_act_B:.1f}%")
        m2.metric("Taux de chômage", f"{taux_chom_B:.1f}%")
        m3.metric("Emplois totaux", f"{int(emplois_B):,}".replace(",", " "))
    
    streamlit.divider()
    
    # Graphiques comparatifs
    col_g1, col_g2 = streamlit.columns(2)
    
    with col_g1:
        # Graphique 1: Répartition population active
        fig_repartition = go.Figure()
        
        fig_repartition.add_trace(go.Bar(
            name=ville_A,
            x=['Actifs occupés', 'Chômeurs', 'Inactifs'],
            y=[actifs_A - chomeurs_A, chomeurs_A, pop15_64_A - actifs_A],
            marker_color='#1f77b4'
        ))
        
        fig_repartition.add_trace(go.Bar(
            name=ville_B,
            x=['Actifs occupés', 'Chômeurs', 'Inactifs'],
            y=[actifs_B - chomeurs_B, chomeurs_B, pop15_64_B - actifs_B],
            marker_color='#ff7f0e'
        ))
        
        fig_repartition.update_layout(
            title="Répartition de la population 15-64 ans",
            barmode='group',
            yaxis_title="Nombre de personnes",
            height=400
        )
        
        streamlit.plotly_chart(fig_repartition, use_container_width=True)
    
    with col_g2:
        # Graphique 2: Taux comparés
        fig_taux = go.Figure()
        
        fig_taux.add_trace(go.Bar(
            name=ville_A,
            x=['Taux d\'activité', 'Taux de chômage'],
            y=[taux_act_A, taux_chom_A],
            marker_color='#1f77b4',
            text=[f"{taux_act_A:.1f}%", f"{taux_chom_A:.1f}%"],
            textposition='auto'
        ))
        
        fig_taux.add_trace(go.Bar(
            name=ville_B,
            x=['Taux d\'activité', 'Taux de chômage'],
            y=[taux_act_B, taux_chom_B],
            marker_color='#ff7f0e',
            text=[f"{taux_act_B:.1f}%", f"{taux_chom_B:.1f}%"],
            textposition='auto'
        ))
        
        fig_taux.update_layout(
            title="Taux d'activité et de chômage",
            barmode='group',
            yaxis_title="Pourcentage (%)",
            height=400
        )
        
        streamlit.plotly_chart(fig_taux, use_container_width=True)
    
    # Graphique 3: Types d'emplois
    streamlit.subheader(" Structure de l'emploi")
    
    fig_emplois = go.Figure()
    
    fig_emplois.add_trace(go.Bar(
        name=ville_A,
        x=['Emplois salariés', 'Emplois non-salariés'],
        y=[emplois_sal_A, emplois_A - emplois_sal_A],
        marker_color='#1f77b4',
        text=[f"{int(emplois_sal_A):,}".replace(",", " "), 
              f"{int(emplois_A - emplois_sal_A):,}".replace(",", " ")],
        textposition='auto'
    ))
    
    fig_emplois.add_trace(go.Bar(
        name=ville_B,
        x=['Emplois salariés', 'Emplois non-salariés'],
        y=[emplois_sal_B, emplois_B - emplois_sal_B],
        marker_color='#ff7f0e',
        text=[f"{int(emplois_sal_B):,}".replace(",", " "), 
              f"{int(emplois_B - emplois_sal_B):,}".replace(",", " ")],
        textposition='auto'
    ))
    
    fig_emplois.update_layout(
        title="Répartition des emplois par statut",
        barmode='group',
        yaxis_title="Nombre d'emplois",
        height=400
    )
    
    streamlit.plotly_chart(fig_emplois, use_container_width=True)

# ============================================================================
# ONGLET 3 : LOGEMENT
# ============================================================================

with onglet3:
    streamlit.header("Indicateurs Logement", divider="blue")
    
    # Récupération des données logement
    log_total_A = temp_A['P22_LOG'].values[0]
    rp_A = temp_A['P22_RP'].values[0]
    rs_A = temp_A['P22_RSECOCC'].values[0]
    vac_A = temp_A['P22_LOGVAC'].values[0]
    prop_A = temp_A['P22_RP_PROP'].values[0]
    
    log_total_B = temp_B['P22_LOG'].values[0]
    rp_B = temp_B['P22_RP'].values[0]
    rs_B = temp_B['P22_RSECOCC'].values[0]
    vac_B = temp_B['P22_LOGVAC'].values[0]
    prop_B = temp_B['P22_RP_PROP'].values[0]
    
    # Taux de vacance et de propriétaires
    taux_vac_A = (vac_A / log_total_A * 100) if log_total_A > 0 else 0
    taux_vac_B = (vac_B / log_total_B * 100) if log_total_B > 0 else 0
    taux_prop_A = (prop_A / rp_A * 100) if rp_A > 0 else 0
    taux_prop_B = (prop_B / rp_B * 100) if rp_B > 0 else 0
    
    # Métriques
    col1, col2 = streamlit.columns(2)
    
    with col1:
        streamlit.subheader(f"🔵 {ville_A}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Logements totaux", f"{int(log_total_A):,}".replace(",", " "))
        m2.metric("Taux de vacance", f"{taux_vac_A:.1f}%")
        m3.metric("Taux propriétaires", f"{taux_prop_A:.1f}%")
    
    with col2:
        streamlit.subheader(f"🟠 {ville_B}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Logements totaux", f"{int(log_total_B):,}".replace(",", " "))
        m2.metric("Taux de vacance", f"{taux_vac_B:.1f}%")
        m3.metric("Taux propriétaires", f"{taux_prop_B:.1f}%")
    
    streamlit.divider()
    
    # Graphiques
    col_g1, col_g2 = streamlit.columns(2)
    
    with col_g1:
        # Graphique 1: Répartition des logements
        fig_log_repartition = go.Figure()
        
        fig_log_repartition.add_trace(go.Bar(
            name=ville_A,
            x=['Résidences principales', 'Rés. secondaires', 'Logements vacants'],
            y=[rp_A, rs_A, vac_A],
            marker_color='#1f77b4'
        ))
        
        fig_log_repartition.add_trace(go.Bar(
            name=ville_B,
            x=['Résidences principales', 'Rés. secondaires', 'Logements vacants'],
            y=[rp_B, rs_B, vac_B],
            marker_color='#ff7f0e'
        ))
        
        fig_log_repartition.update_layout(
            title="Répartition des logements par type",
            barmode='group',
            yaxis_title="Nombre de logements",
            height=400
        )
        
        streamlit.plotly_chart(fig_log_repartition, use_container_width=True)
    
    with col_g2:
        # Graphique 2: Camemberts propriétaires/locataires
        labels = ['Propriétaires', 'Locataires']
        
        fig_statut = go.Figure()
        
        fig_statut.add_trace(go.Pie(
            labels=labels,
            values=[prop_A, rp_A - prop_A],
            name=ville_A,
            domain={'x': [0, 0.45]},
            marker_colors=['#1f77b4', '#aec7e8'],
            title=ville_A
        ))
        
        fig_statut.add_trace(go.Pie(
            labels=labels,
            values=[prop_B, rp_B - prop_B],
            name=ville_B,
            domain={'x': [0.55, 1]},
            marker_colors=['#ff7f0e', '#ffbb78'],
            title=ville_B
        ))
        
        fig_statut.update_layout(
            title="Statut d'occupation des résidences principales",
            height=400
        )
        
        streamlit.plotly_chart(fig_statut, use_container_width=True)
    
    # Graphique 3: Taux comparés
    streamlit.subheader("📊 Indicateurs comparatifs")
    
    fig_taux_log = go.Figure()
    
    fig_taux_log.add_trace(go.Bar(
        name=ville_A,
        x=['Taux de vacance', 'Taux de propriétaires'],
        y=[taux_vac_A, taux_prop_A],
        marker_color='#1f77b4',
        text=[f"{taux_vac_A:.1f}%", f"{taux_prop_A:.1f}%"],
        textposition='auto'
    ))
    
    fig_taux_log.add_trace(go.Bar(
        name=ville_B,
        x=['Taux de vacance', 'Taux de propriétaires'],
        y=[taux_vac_B, taux_prop_B],
        marker_color='#ff7f0e',
        text=[f"{taux_vac_B:.1f}%", f"{taux_prop_B:.1f}%"],
        textposition='auto'
    ))
    
    fig_taux_log.update_layout(
        title="Comparaison des taux",
        barmode='group',
        yaxis_title="Pourcentage (%)",
        height=400
    )
    
    streamlit.plotly_chart(fig_taux_log, use_container_width=True)

# ============================================================================
# ONGLET 4 : MÉTÉO
# ============================================================================

with onglet4:
    streamlit.header("Conditions Météorologiques", divider="blue")
    
    streamlit.info("🌍 Données météo en temps réel via Open-Meteo API (prévisions sur 5 jours)")
    
    col1, col2 = streamlit.columns(2)
    
    # Météo ville A
    with col1:
        streamlit.subheader(f"🔵 {ville_A}")
        
        lat_A = temp_A['latitude'].values[0]
        lon_A = temp_A['longitude'].values[0]
        meteo_A = obtenir_meteo(ville_A, lat_A, lon_A)
        
        if meteo_A and 'daily' in meteo_A:
            daily = meteo_A['daily']
            
            # Affichage des prévisions
            for i in range(min(5, len(daily['time']))):
                date = daily['time'][i]
                temp_max = daily['temperature_2m_max'][i]
                temp_min = daily['temperature_2m_min'][i]
                precip = daily['precipitation_sum'][i]
                weather_code = daily['weathercode'][i]
                emoji = code_meteo_vers_emoji(weather_code)
                
                with streamlit.expander(f"{emoji} {date} - {temp_min:.0f}°C / {temp_max:.0f}°C", expanded=(i == 0)):
                    c1, c2, c3 = streamlit.columns(3)
                    c1.metric("🌡️ Max", f"{temp_max:.1f}°C")
                    c2.metric("🌡️ Min", f"{temp_min:.1f}°C")
                    c3.metric("🌧️ Précip.", f"{precip:.1f} mm")
            
            # Graphique températures
            fig_temp_A = go.Figure()
            fig_temp_A.add_trace(go.Scatter(
                x=daily['time'][:5],
                y=daily['temperature_2m_max'][:5],
                mode='lines+markers',
                name='Temp. max',
                line=dict(color='red', width=2),
                marker=dict(size=8)
            ))
            fig_temp_A.add_trace(go.Scatter(
                x=daily['time'][:5],
                y=daily['temperature_2m_min'][:5],
                mode='lines+markers',
                name='Temp. min',
                line=dict(color='blue', width=2),
                marker=dict(size=8)
            ))
            fig_temp_A.update_layout(
                title=f"Évolution des températures - {ville_A}",
                xaxis_title="Date",
                yaxis_title="Température (°C)",
                height=300
            )
            streamlit.plotly_chart(fig_temp_A, use_container_width=True)
        else:
            streamlit.error("❌ Impossible de récupérer les données météo")
    
    # Météo ville B
    with col2:
        streamlit.subheader(f"🟠 {ville_B}")
        
        lat_B = temp_B['latitude'].values[0]
        lon_B = temp_B['longitude'].values[0]
        meteo_B = obtenir_meteo(ville_B, lat_B, lon_B)
        
        if meteo_B and 'daily' in meteo_B:
            daily = meteo_B['daily']
            
            # Affichage des prévisions
            for i in range(min(5, len(daily['time']))):
                date = daily['time'][i]
                temp_max = daily['temperature_2m_max'][i]
                temp_min = daily['temperature_2m_min'][i]
                precip = daily['precipitation_sum'][i]
                weather_code = daily['weathercode'][i]
                emoji = code_meteo_vers_emoji(weather_code)
                
                with streamlit.expander(f"{emoji} {date} - {temp_min:.0f}°C / {temp_max:.0f}°C", expanded=(i == 0)):
                    c1, c2, c3 = streamlit.columns(3)
                    c1.metric("🌡️ Max", f"{temp_max:.1f}°C")
                    c2.metric("🌡️ Min", f"{temp_min:.1f}°C")
                    c3.metric("🌧️ Précip.", f"{precip:.1f} mm")
            
            # Graphique températures
            fig_temp_B = go.Figure()
            fig_temp_B.add_trace(go.Scatter(
                x=daily['time'][:5],
                y=daily['temperature_2m_max'][:5],
                mode='lines+markers',
                name='Temp. max',
                line=dict(color='red', width=2),
                marker=dict(size=8)
            ))
            fig_temp_B.add_trace(go.Scatter(
                x=daily['time'][:5],
                y=daily['temperature_2m_min'][:5],
                mode='lines+markers',
                name='Temp. min',
                line=dict(color='blue', width=2),
                marker=dict(size=8)
            ))
            fig_temp_B.update_layout(
                title=f"Évolution des températures - {ville_B}",
                xaxis_title="Date",
                yaxis_title="Température (°C)",
                height=300
            )
            streamlit.plotly_chart(fig_temp_B, use_container_width=True)
        else:
            streamlit.error("❌ Impossible de récupérer les données météo")
    
    streamlit.divider()
    streamlit.caption("📡 Données météo fournies par Open-Meteo.com")


# ============================================================================
# ONGLET 5 : Formation
# ============================================================================

with onglet5:
    streamlit.header("Indicateurs Formation", divider="blue")

# ============================================================================
# ONGLET 6 : Sports
# ============================================================================

with onglet6:
    streamlit.header("Indicateurs Sports", divider="blue")

# ============================================================================
# ONGLET 7 : Culture
# ============================================================================

with onglet7:
    streamlit.header("Indicateurs Culture", divider="blue")


# ============================================================================
# ONGLET 8 : Tourisme
# ============================================================================

with onglet8:
    streamlit.header("Indicateurs Tourisme", divider="blue")
