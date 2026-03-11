"""
Application Streamlit - Comparateur de Villes Françaises
Projet noté BUT SD2 VCOD - Programmation Web

Auteurs: Octave, Ely, Camille
Date: Mars 2026
"""

import streamlit
import pandas
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import numpy

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

streamlit.set_page_config(
    page_title="Comparateur de Villes Françaises",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════════
# CSS PERSONNALISÉ
# ═══════════════════════════════════════════════════════════════════════════════

streamlit.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    .stApp {
        background: linear-gradient(160deg, #f8fafc 0%, #eef2ff 50%, #f5f3ff 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%) !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown {
        color: rgba(255,255,255,0.9) !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.12) !important;
    }
    section[data-testid="stSidebar"] .stAlert {
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.12) !important;
    }

    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    }
    [data-testid="stMetricValue"] { font-weight: 700 !important; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2px; background: white;
        border-radius: 14px; padding: 4px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px; font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    }
    .stTabs [aria-selected="true"] p {
        color: white !important; font-weight: 600 !important;
    }

    [data-testid="stPlotlyChart"] {
        background: white;
        border-radius: 14px;
        padding: 0.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    h1 { letter-spacing: -1px !important; }
    h2 { letter-spacing: -0.5px !important; }
    .stAlert { border-radius: 12px !important; }
    .streamlit-expanderHeader { border-radius: 10px !important; }
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES COULEURS
# ═══════════════════════════════════════════════════════════════════════════════

COULEUR_A = '#6366f1'   # Indigo
COULEUR_B = '#f97316'   # Orange

SECTEURS_LABELS = {
    'ETAZ23': 'Agriculture',
    'ETBE23': 'Industrie',
    'ETFZ23': 'Construction',
    'ETGU23': 'Commerce & Services',
    'ETOQ23': 'Administration',
}

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS DE CHARGEMENT DES DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@streamlit.cache_data
def charger_donnees():
    """Charge et fusionne données INSEE + GPS, filtre > 20 000 hab."""
    data_insee = pandas.read_csv("base_cc_comparateur.csv", sep=";", low_memory=False)
    data_gps = pandas.read_csv("20230823-communes-departement-region.csv", sep=",")
    data_gps["code_commune_INSEE"] = data_gps["code_commune_INSEE"].astype(str).str.zfill(5)
    data_insee["CODGEO"] = data_insee["CODGEO"].astype(str).str.zfill(5)
    data_20k = data_insee.query("P22_POP > 20000")
    result = pandas.merge(data_20k, data_gps, left_on="CODGEO", right_on="code_commune_INSEE", how="inner")
    return result.drop_duplicates(subset=['CODGEO']).sort_values(by="nom_commune_complet")


@streamlit.cache_data
def charger_formations():
    """Charge les données Parcoursup."""
    return pandas.read_csv("base_formation_parcoursup.csv", sep=";", low_memory=False)


@streamlit.cache_data(ttl=3600)
def obtenir_meteo(ville_nom, latitude, longitude):
    """Prévisions météo via Open-Meteo API."""
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": latitude, "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone": "Europe/Paris", "forecast_days": 5
        }, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def code_meteo_vers_emoji(code):
    """Code WMO -> emoji."""
    return {
        0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
        45: "🌫️", 48: "🌫️", 51: "🌦️", 53: "🌧️", 55: "🌧️",
        61: "🌧️", 63: "🌧️", 65: "🌧️", 71: "🌨️", 73: "🌨️", 75: "🌨️",
        80: "🌦️", 81: "🌧️", 82: "⛈️", 95: "⛈️", 96: "⛈️", 99: "⛈️"
    }.get(code, "🌡️")


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS API EXTERNES
# ═══════════════════════════════════════════════════════════════════════════════

@streamlit.cache_data(ttl=3600, show_spinner=False)
def obtenir_equipements_sportifs(commune_nom):
    """Équipements sportifs via data.sports.gouv.fr."""
    try:
        tous_records = []
        offset = 0
        while True:
            r = requests.get(
                "https://data.sports.gouv.fr/api/explore/v2.1/catalog/datasets/equipements-sportifs/records",
                params={"where": f'new_name="{commune_nom.title()}"', "limit": 100, "offset": offset},
                timeout=10
            )
            r.raise_for_status()
            data = r.json()
            records = data.get('results', [])
            if not records:
                break
            tous_records.extend(records)
            if len(tous_records) >= data.get('total_count', 0):
                break
            offset += 100
        if not tous_records:
            return pandas.DataFrame()
        df = pandas.DataFrame(tous_records)
        colonnes_utiles = ['inst_nom', 'equip_nom', 'equip_type_name', 'equip_nature',
                           'equip_prop_type', 'gen_2024fin_labellisation', 'equip_coordonnees']
        colonnes_presentes = [c for c in colonnes_utiles if c in df.columns]
        df = df[colonnes_presentes]
        if 'equip_type_name' in df.columns:
            df = df.dropna(subset=['equip_type_name'])
            df = df[df['equip_type_name'].astype(str).str.strip() != '']
        return df
    except Exception:
        return pandas.DataFrame()


@streamlit.cache_data(ttl=3600, show_spinner=False)
def obtenir_lieux_touristiques(lat, lon, rayon=10000):
    """Lieux touristiques via Overpass API (OpenStreetMap)."""
    types_exclus = {'yes', 'information', 'apartment', 'caravan_site', 'picnic_site'}
    try:
        query = f'[out:json][timeout:10];node["tourism"](around:{rayon},{lat},{lon});out body;'
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=15)
        r.raise_for_status()
        elements = r.json().get('elements', [])
        lieux = []
        for el in elements:
            tags = el.get('tags', {})
            nom = tags.get('name', '').strip()
            type_lieu = tags.get('tourism', 'autre').strip()
            if nom and type_lieu not in types_exclus:
                lieux.append({
                    'nom': nom,
                    'type': type_lieu,
                    'lat': el.get('lat'),
                    'lon': el.get('lon')
                })
        return pandas.DataFrame(lieux) if lieux else pandas.DataFrame()
    except Exception:
        return pandas.DataFrame()


LABELS_TOURISME = {
    'hotel': 'Hôtel', 'motel': 'Motel', 'hostel': 'Auberge',
    'guest_house': "Maison d'hôtes", 'apartment': 'Appartement',
    'attraction': 'Attraction', 'museum': 'Musée',
    'gallery': 'Galerie', 'artwork': "Œuvre d'art",
    'viewpoint': 'Point de vue', 'information': 'Office tourisme',
    'camp_site': 'Camping', 'caravan_site': 'Aire camping-car',
    'picnic_site': 'Aire pique-nique', 'theme_park': 'Parc à thème',
}

# ═══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

villes_data = charger_donnees()
formations_data = charger_formations()
liste_villes = list(villes_data["nom_commune_complet"])

# Cross-filtering : appliquer le clic sur barre AVANT la création du widget radio
if '_pending_mise_en_avant' in streamlit.session_state:
    streamlit.session_state['mise_en_avant'] = streamlit.session_state.pop('_pending_mise_en_avant')

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with streamlit.sidebar:
    streamlit.title("🏙️ Comparateur")
    streamlit.markdown("---")
    streamlit.subheader("Sélection des villes")

    default_A = liste_villes.index("Niort") if "Niort" in liste_villes else 0
    default_B = liste_villes.index("Bordeaux") if "Bordeaux" in liste_villes else min(1, len(liste_villes) - 1)

    ville_A = streamlit.selectbox("🔵 Ville A", liste_villes, index=default_A, key="ville_a")
    ville_B = streamlit.selectbox("🟠 Ville B", liste_villes, index=default_B, key="ville_b")

    streamlit.markdown("---")
    streamlit.subheader("🎯 Mise en avant")
    mise_en_avant = streamlit.radio(
        "Isoler une ville sur tous les graphiques :",
        ["Les deux", ville_A, ville_B],
        key="mise_en_avant",
        horizontal=True
    )

    streamlit.markdown("---")
    streamlit.info(f"📊 {len(liste_villes)} villes disponibles\n(> 20 000 habitants)")
    streamlit.caption("Projet BUT SD2 VCOD — Mars 2026")

# Données des villes sélectionnées
temp_A = villes_data.query("nom_commune_complet == @ville_A")
temp_B = villes_data.query("nom_commune_complet == @ville_B")

# Opacité globale
opacity_A = 1.0 if mise_en_avant in ["Les deux", ville_A] else 0.15
opacity_B = 1.0 if mise_en_avant in ["Les deux", ville_B] else 0.15

# Coordonnées
lat_A, lon_A = temp_A['latitude'].values[0], temp_A['longitude'].values[0]
lat_B, lon_B = temp_B['latitude'].values[0], temp_B['longitude'].values[0]

# ═══════════════════════════════════════════════════════════════════════════════
# ONGLETS
# ═══════════════════════════════════════════════════════════════════════════════

onglet1, onglet2, onglet3, onglet4, onglet5, onglet6, onglet7, onglet8 = streamlit.tabs([
    "📍 Généralités", "💼 Emploi", "🏠 Logement", "🌦️ Météo",
    "🎓 Formation", "🏅 Sports", "🧭 Tourisme", "🏆 Classement"
])


def style_figure(fig, hauteur=450):
    """Applique le style commun aux figures."""
    fig.update_layout(
        barmode='group', height=hauteur,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif'),
        margin=dict(t=40, b=40),
        clickmode='event+select',
        transition_duration=400,
    )
    fig.update_traces(selected=dict(marker=dict(opacity=1.0)),
                      unselected=dict(marker=dict(opacity=1.0)))


def afficher_graphique(fig, chart_key):
    """Affiche un graphique plotly avec cross-filtering par clic sur barre."""
    event = streamlit.plotly_chart(fig, use_container_width=True, key=chart_key, on_select="rerun", selection_mode=["points"])
    try:
        points = event.selection.points if event and event.selection else []
    except Exception:
        points = []
    if points:
        pt = points[0]
        curve_num = pt.get('curve_number', pt.get('curveNumber', 0))
        clicked_ville = ville_A if curve_num % 2 == 0 else ville_B
        current = streamlit.session_state.get('mise_en_avant', 'Les deux')
        if current == clicked_ville:
            streamlit.session_state['_pending_mise_en_avant'] = 'Les deux'
        else:
            streamlit.session_state['_pending_mise_en_avant'] = clicked_ville
        streamlit.rerun()


def fmt(val):
    """Formate un nombre avec des espaces."""
    return f"{int(val):,}".replace(",", " ")


def delta_str(val_a, val_b, suffix="", inverse=False):
    """Calcule le delta A vs B pour les metrics."""
    try:
        diff = float(val_a) - float(val_b)
    except (ValueError, TypeError):
        return None
    if inverse:
        diff = -diff
    if abs(diff) < 0.01:
        return None
    return f"{diff:+,.0f}{suffix}".replace(",", " ") if suffix != "%" else f"{diff:+.1f}{suffix}"


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 1 : GÉNÉRALITÉS & CARTE
# ═══════════════════════════════════════════════════════════════════════════════

with onglet1:
    streamlit.header("Informations Générales", divider="blue")

    pop_A, pop_B = int(temp_A['P22_POP'].values[0]), int(temp_B['P22_POP'].values[0])
    sup_A, sup_B = int(temp_A['SUPERF'].values[0]), int(temp_B['SUPERF'].values[0])
    densite_A = int(pop_A / sup_A) if sup_A > 0 else 0
    densite_B = int(pop_B / sup_B) if sup_B > 0 else 0
    men_A, men_B = int(temp_A['P22_MEN'].values[0]), int(temp_B['P22_MEN'].values[0])
    rev_A, rev_B = int(temp_A['MED21'].values[0]), int(temp_B['MED21'].values[0])

    col1, col2 = streamlit.columns(2)
    with col1:
        streamlit.subheader(f"🔵 {ville_A}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Population", fmt(pop_A), delta=delta_str(pop_A, pop_B))
        m2.metric("Superficie (km²)", fmt(sup_A))
        m3.metric("Densité (hab/km²)", fmt(densite_A), delta=delta_str(densite_A, densite_B))
        m4, m5 = streamlit.columns(2)
        m4.metric("Ménages", fmt(men_A), delta=delta_str(men_A, men_B))
        m5.metric("Revenu médian", f"{fmt(rev_A)} €", delta=delta_str(rev_A, rev_B, " €"))

    with col2:
        streamlit.subheader(f"🟠 {ville_B}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Population", fmt(pop_B), delta=delta_str(pop_B, pop_A))
        m2.metric("Superficie (km²)", fmt(sup_B))
        m3.metric("Densité (hab/km²)", fmt(densite_B), delta=delta_str(densite_B, densite_A))
        m4, m5 = streamlit.columns(2)
        m4.metric("Ménages", fmt(men_B), delta=delta_str(men_B, men_A))
        m5.metric("Revenu médian", f"{fmt(rev_B)} €", delta=delta_str(rev_B, rev_A, " €"))

    # ─── Radar chart synthèse ───
    streamlit.divider()
    streamlit.subheader("🕸️ Profil comparatif")

    # Normaliser les indicateurs entre 0 et 1 par rapport à toutes les villes
    indicateurs_radar = {
        'Population': ('P22_POP', False),
        'Revenu médian': ('MED21', False),
        'Taux activité': (None, False),  # calculé
        'Emplois': ('P22_EMPLT', False),
        'Logements': ('P22_LOG', False),
        'Ménages': ('P22_MEN', False),
    }

    def normaliser(val, col_name):
        """Normalise une valeur entre 0 et 100 par rapport au min/max de toutes les villes."""
        val = pandas.to_numeric(val, errors='coerce')
        if pandas.isna(val):
            return 50
        col_data = pandas.to_numeric(villes_data[col_name], errors='coerce').dropna()
        vmin, vmax = col_data.min(), col_data.max()
        if vmax == vmin:
            return 50
        return float((val - vmin) / (vmax - vmin) * 100)

    actifs_A_r = temp_A['P22_ACT1564'].values[0]
    pop1564_A_r = temp_A['P22_POP1564'].values[0]
    actifs_B_r = temp_B['P22_ACT1564'].values[0]
    pop1564_B_r = temp_B['P22_POP1564'].values[0]
    taux_act_A_r = (actifs_A_r / pop1564_A_r * 100) if pop1564_A_r > 0 else 0
    taux_act_B_r = (actifs_B_r / pop1564_B_r * 100) if pop1564_B_r > 0 else 0

    # Calculer les scores normalisés
    categories_radar = list(indicateurs_radar.keys())
    scores_A, scores_B = [], []
    for cat, (col, _) in indicateurs_radar.items():
        if cat == 'Taux activité':
            # Normaliser entre 50% et 85% (plage réaliste)
            scores_A.append(max(0, min(100, (taux_act_A_r - 50) / 35 * 100)))
            scores_B.append(max(0, min(100, (taux_act_B_r - 50) / 35 * 100)))
        else:
            scores_A.append(normaliser(temp_A[col].values[0], col))
            scores_B.append(normaliser(temp_B[col].values[0], col))

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=scores_A + [scores_A[0]], theta=categories_radar + [categories_radar[0]],
        fill='toself', name=ville_A,
        line=dict(color=COULEUR_A, width=2),
        fillcolor=f'rgba(99, 102, 241, {0.25 * opacity_A})',
        opacity=opacity_A
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=scores_B + [scores_B[0]], theta=categories_radar + [categories_radar[0]],
        fill='toself', name=ville_B,
        line=dict(color=COULEUR_B, width=2),
        fillcolor=f'rgba(249, 115, 22, {0.25 * opacity_B})',
        opacity=opacity_B
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)),
        height=420, margin=dict(t=40, b=40, l=60, r=60),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif'),
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5)
    )
    streamlit.plotly_chart(fig_radar, use_container_width=True)

    # ─── Carte ───
    streamlit.divider()
    streamlit.subheader("🗺️ Localisation géographique")

    villes_comparees = pandas.concat([temp_A, temp_B])
    fig_carte = px.scatter_mapbox(
        villes_comparees, lat="latitude", lon="longitude",
        hover_name="nom_commune_complet",
        hover_data={"latitude": False, "longitude": False, "P22_POP": ":,", "nom_departement": True},
        size="P22_POP", color="nom_commune_complet",
        color_discrete_map={ville_A: COULEUR_A, ville_B: COULEUR_B},
        zoom=5.5, height=500, mapbox_style="carto-positron"
    )
    fig_carte.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    streamlit.plotly_chart(fig_carte, use_container_width=True)

    # ─── Export CSV ───
    streamlit.divider()
    streamlit.subheader("📥 Exporter les données")
    export_data = pandas.DataFrame({
        'Indicateur': ['Population', 'Superficie (km²)', 'Densité (hab/km²)', 'Ménages', 'Revenu médian (€)'],
        ville_A: [pop_A, sup_A, densite_A, men_A, rev_A],
        ville_B: [pop_B, sup_B, densite_B, men_B, rev_B],
        'Écart': [pop_A - pop_B, sup_A - sup_B, densite_A - densite_B, men_A - men_B, rev_A - rev_B],
    })
    streamlit.download_button(
        "📥 Télécharger le comparatif (CSV)",
        export_data.to_csv(index=False, sep=";").encode('utf-8'),
        file_name=f"comparatif_{ville_A}_{ville_B}.csv",
        mime="text/csv"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 2 : EMPLOI
# ═══════════════════════════════════════════════════════════════════════════════

with onglet2:
    streamlit.header("Indicateurs Emploi", divider="blue")

    pop15_64_A, actifs_A, chomeurs_A = temp_A['P22_POP1564'].values[0], temp_A['P22_ACT1564'].values[0], temp_A['P22_CHOM1564'].values[0]
    emplois_A, emplois_sal_A = temp_A['P22_EMPLT'].values[0], temp_A['P22_EMPLT_SAL'].values[0]
    pop15_64_B, actifs_B, chomeurs_B = temp_B['P22_POP1564'].values[0], temp_B['P22_ACT1564'].values[0], temp_B['P22_CHOM1564'].values[0]
    emplois_B, emplois_sal_B = temp_B['P22_EMPLT'].values[0], temp_B['P22_EMPLT_SAL'].values[0]

    taux_chom_A = (chomeurs_A / actifs_A * 100) if actifs_A > 0 else 0
    taux_chom_B = (chomeurs_B / actifs_B * 100) if actifs_B > 0 else 0
    taux_act_A = (actifs_A / pop15_64_A * 100) if pop15_64_A > 0 else 0
    taux_act_B = (actifs_B / pop15_64_B * 100) if pop15_64_B > 0 else 0

    col1, col2 = streamlit.columns(2)
    with col1:
        streamlit.subheader(f"🔵 {ville_A}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Taux d'activité", f"{taux_act_A:.1f}%", delta=delta_str(taux_act_A, taux_act_B, "%"))
        m2.metric("Taux de chômage", f"{taux_chom_A:.1f}%", delta=delta_str(taux_chom_A, taux_chom_B, "%"), delta_color="inverse")
        m3.metric("Emplois totaux", fmt(emplois_A), delta=delta_str(emplois_A, emplois_B))
    with col2:
        streamlit.subheader(f"🟠 {ville_B}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Taux d'activité", f"{taux_act_B:.1f}%", delta=delta_str(taux_act_B, taux_act_A, "%"))
        m2.metric("Taux de chômage", f"{taux_chom_B:.1f}%", delta=delta_str(taux_chom_B, taux_chom_A, "%"), delta_color="inverse")
        m3.metric("Emplois totaux", fmt(emplois_B), delta=delta_str(emplois_B, emplois_A))

    streamlit.divider()
    streamlit.subheader("📊 Comparaison détaillée")
    streamlit.caption("💡 Cliquez sur une barre pour isoler cette ville sur tous les graphiques.")

    fig_emploi = make_subplots(rows=1, cols=3,
        subplot_titles=("Répartition 15-64 ans", "Taux d'activité / chômage", "Structure de l'emploi"))

    fig_emploi.add_trace(go.Bar(name=ville_A, x=['Actifs occupés', 'Chômeurs', 'Inactifs'],
        y=[actifs_A - chomeurs_A, chomeurs_A, pop15_64_A - actifs_A],
        marker_color=COULEUR_A, opacity=opacity_A, legendgroup='A'), row=1, col=1)
    fig_emploi.add_trace(go.Bar(name=ville_B, x=['Actifs occupés', 'Chômeurs', 'Inactifs'],
        y=[actifs_B - chomeurs_B, chomeurs_B, pop15_64_B - actifs_B],
        marker_color=COULEUR_B, opacity=opacity_B, legendgroup='B'), row=1, col=1)

    fig_emploi.add_trace(go.Bar(name=ville_A, x=["Taux d'activité", "Taux de chômage"],
        y=[taux_act_A, taux_chom_A], text=[f"{taux_act_A:.1f}%", f"{taux_chom_A:.1f}%"], textposition='auto',
        marker_color=COULEUR_A, opacity=opacity_A, legendgroup='A', showlegend=False), row=1, col=2)
    fig_emploi.add_trace(go.Bar(name=ville_B, x=["Taux d'activité", "Taux de chômage"],
        y=[taux_act_B, taux_chom_B], text=[f"{taux_act_B:.1f}%", f"{taux_chom_B:.1f}%"], textposition='auto',
        marker_color=COULEUR_B, opacity=opacity_B, legendgroup='B', showlegend=False), row=1, col=2)

    fig_emploi.add_trace(go.Bar(name=ville_A, x=['Salariés', 'Non-salariés'],
        y=[emplois_sal_A, emplois_A - emplois_sal_A],
        marker_color=COULEUR_A, opacity=opacity_A, legendgroup='A', showlegend=False), row=1, col=3)
    fig_emploi.add_trace(go.Bar(name=ville_B, x=['Salariés', 'Non-salariés'],
        y=[emplois_sal_B, emplois_B - emplois_sal_B],
        marker_color=COULEUR_B, opacity=opacity_B, legendgroup='B', showlegend=False), row=1, col=3)

    style_figure(fig_emploi)
    afficher_graphique(fig_emploi, "chart_emploi")

    # ─── Secteurs d'activité ───
    streamlit.divider()
    streamlit.subheader("🏭 Établissements par secteur d'activité")

    secteurs_cols = [c for c in SECTEURS_LABELS.keys() if c in temp_A.columns and c in temp_B.columns]
    if secteurs_cols:
        labels_sec = [SECTEURS_LABELS[c] for c in secteurs_cols]
        vals_sec_A = [pandas.to_numeric(temp_A[c].values[0], errors='coerce') or 0 for c in secteurs_cols]
        vals_sec_B = [pandas.to_numeric(temp_B[c].values[0], errors='coerce') or 0 for c in secteurs_cols]

        fig_secteur = go.Figure()
        fig_secteur.add_trace(go.Bar(name=ville_A, x=labels_sec, y=vals_sec_A,
            marker_color=COULEUR_A, opacity=opacity_A, text=[fmt(v) for v in vals_sec_A], textposition='auto'))
        fig_secteur.add_trace(go.Bar(name=ville_B, x=labels_sec, y=vals_sec_B,
            marker_color=COULEUR_B, opacity=opacity_B, text=[fmt(v) for v in vals_sec_B], textposition='auto'))
        style_figure(fig_secteur, 400)
        afficher_graphique(fig_secteur, "chart_secteur")

    # ─── Évolution temporelle ───
    pop16_A = pandas.to_numeric(temp_A['P16_POP'].values[0], errors='coerce')
    pop16_B = pandas.to_numeric(temp_B['P16_POP'].values[0], errors='coerce')
    emp16_A = pandas.to_numeric(temp_A['P16_EMPLT'].values[0], errors='coerce')
    emp16_B = pandas.to_numeric(temp_B['P16_EMPLT'].values[0], errors='coerce')

    if not pandas.isna(pop16_A) and not pandas.isna(pop16_B):
        streamlit.divider()
        streamlit.subheader("📈 Évolution 2016 → 2022")

        fig_evol = make_subplots(rows=1, cols=2,
            subplot_titles=("Population", "Emplois"))

        fig_evol.add_trace(go.Scatter(x=['2016', '2022'], y=[pop16_A, pop_A],
            mode='lines+markers+text', name=ville_A, text=[fmt(pop16_A), fmt(pop_A)], textposition='top center',
            line=dict(color=COULEUR_A, width=3), marker=dict(size=10), opacity=opacity_A), row=1, col=1)
        fig_evol.add_trace(go.Scatter(x=['2016', '2022'], y=[pop16_B, pop_B],
            mode='lines+markers+text', name=ville_B, text=[fmt(pop16_B), fmt(pop_B)], textposition='top center',
            line=dict(color=COULEUR_B, width=3), marker=dict(size=10), opacity=opacity_B), row=1, col=1)

        if not pandas.isna(emp16_A) and not pandas.isna(emp16_B):
            fig_evol.add_trace(go.Scatter(x=['2016', '2022'], y=[emp16_A, emplois_A],
                mode='lines+markers+text', name=ville_A, text=[fmt(emp16_A), fmt(emplois_A)], textposition='top center',
                line=dict(color=COULEUR_A, width=3), marker=dict(size=10), opacity=opacity_A, showlegend=False), row=1, col=2)
            fig_evol.add_trace(go.Scatter(x=['2016', '2022'], y=[emp16_B, emplois_B],
                mode='lines+markers+text', name=ville_B, text=[fmt(emp16_B), fmt(emplois_B)], textposition='top center',
                line=dict(color=COULEUR_B, width=3), marker=dict(size=10), opacity=opacity_B, showlegend=False), row=1, col=2)

        fig_evol.update_layout(
            height=380, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif'), margin=dict(t=40, b=40),
        )
        streamlit.plotly_chart(fig_evol, use_container_width=True)

        # Metrics évolution
        evol_pop_A = (pop_A - pop16_A) / pop16_A * 100 if pop16_A > 0 else 0
        evol_pop_B = (pop_B - pop16_B) / pop16_B * 100 if pop16_B > 0 else 0
        c1, c2 = streamlit.columns(2)
        c1.metric(f"Évolution population {ville_A}", f"{evol_pop_A:+.1f}%")
        c2.metric(f"Évolution population {ville_B}", f"{evol_pop_B:+.1f}%")


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 3 : LOGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

with onglet3:
    streamlit.header("Indicateurs Logement", divider="blue")

    log_total_A, rp_A, rs_A = temp_A['P22_LOG'].values[0], temp_A['P22_RP'].values[0], temp_A['P22_RSECOCC'].values[0]
    vac_A, prop_A = temp_A['P22_LOGVAC'].values[0], temp_A['P22_RP_PROP'].values[0]
    log_total_B, rp_B, rs_B = temp_B['P22_LOG'].values[0], temp_B['P22_RP'].values[0], temp_B['P22_RSECOCC'].values[0]
    vac_B, prop_B = temp_B['P22_LOGVAC'].values[0], temp_B['P22_RP_PROP'].values[0]

    taux_vac_A = (vac_A / log_total_A * 100) if log_total_A > 0 else 0
    taux_vac_B = (vac_B / log_total_B * 100) if log_total_B > 0 else 0
    taux_prop_A = (prop_A / rp_A * 100) if rp_A > 0 else 0
    taux_prop_B = (prop_B / rp_B * 100) if rp_B > 0 else 0

    col1, col2 = streamlit.columns(2)
    with col1:
        streamlit.subheader(f"🔵 {ville_A}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Logements totaux", fmt(log_total_A), delta=delta_str(log_total_A, log_total_B))
        m2.metric("Taux de vacance", f"{taux_vac_A:.1f}%", delta=delta_str(taux_vac_A, taux_vac_B, "%"), delta_color="inverse")
        m3.metric("Taux propriétaires", f"{taux_prop_A:.1f}%", delta=delta_str(taux_prop_A, taux_prop_B, "%"))
    with col2:
        streamlit.subheader(f"🟠 {ville_B}")
        m1, m2, m3 = streamlit.columns(3)
        m1.metric("Logements totaux", fmt(log_total_B), delta=delta_str(log_total_B, log_total_A))
        m2.metric("Taux de vacance", f"{taux_vac_B:.1f}%", delta=delta_str(taux_vac_B, taux_vac_A, "%"), delta_color="inverse")
        m3.metric("Taux propriétaires", f"{taux_prop_B:.1f}%", delta=delta_str(taux_prop_B, taux_prop_A, "%"))

    streamlit.divider()
    streamlit.subheader("📊 Détails des logements")

    fig_log = make_subplots(rows=1, cols=3,
        subplot_titles=("Répartition", "Statut d'occupation", "Taux comparatifs"))

    fig_log.add_trace(go.Bar(name=ville_A, x=['Rés. principales', 'Rés. secondaires', 'Vacants'],
        y=[rp_A, rs_A, vac_A], marker_color=COULEUR_A, opacity=opacity_A, legendgroup='A'), row=1, col=1)
    fig_log.add_trace(go.Bar(name=ville_B, x=['Rés. principales', 'Rés. secondaires', 'Vacants'],
        y=[rp_B, rs_B, vac_B], marker_color=COULEUR_B, opacity=opacity_B, legendgroup='B'), row=1, col=1)

    fig_log.add_trace(go.Bar(name=ville_A, x=['Propriétaires', 'Locataires'],
        y=[prop_A, rp_A - prop_A], marker_color=COULEUR_A, opacity=opacity_A, legendgroup='A', showlegend=False), row=1, col=2)
    fig_log.add_trace(go.Bar(name=ville_B, x=['Propriétaires', 'Locataires'],
        y=[prop_B, rp_B - prop_B], marker_color=COULEUR_B, opacity=opacity_B, legendgroup='B', showlegend=False), row=1, col=2)

    fig_log.add_trace(go.Bar(name=ville_A, x=['Taux vacance', 'Taux propriétaires'],
        y=[taux_vac_A, taux_prop_A], text=[f"{taux_vac_A:.1f}%", f"{taux_prop_A:.1f}%"], textposition='auto',
        marker_color=COULEUR_A, opacity=opacity_A, legendgroup='A', showlegend=False), row=1, col=3)
    fig_log.add_trace(go.Bar(name=ville_B, x=['Taux vacance', 'Taux propriétaires'],
        y=[taux_vac_B, taux_prop_B], text=[f"{taux_vac_B:.1f}%", f"{taux_prop_B:.1f}%"], textposition='auto',
        marker_color=COULEUR_B, opacity=opacity_B, legendgroup='B', showlegend=False), row=1, col=3)

    style_figure(fig_log)
    afficher_graphique(fig_log, "chart_logement")


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 4 : MÉTÉO
# ═══════════════════════════════════════════════════════════════════════════════

with onglet4:
    streamlit.header("Conditions Météorologiques", divider="blue")
    streamlit.info("🌍 Données en temps réel via Open-Meteo API (prévisions 5 jours)")

    col1, col2 = streamlit.columns(2)

    for col_widget, ville, lat, lon, couleur in [
        (col1, ville_A, lat_A, lon_A, COULEUR_A),
        (col2, ville_B, lat_B, lon_B, COULEUR_B)
    ]:
        with col_widget:
            emoji_ville = "🔵" if ville == ville_A else "🟠"
            streamlit.subheader(f"{emoji_ville} {ville}")
            meteo = obtenir_meteo(ville, lat, lon)

            if meteo and 'daily' in meteo:
                daily = meteo['daily']
                for i in range(min(5, len(daily['time']))):
                    d = daily['time'][i]
                    tmax, tmin = daily['temperature_2m_max'][i], daily['temperature_2m_min'][i]
                    precip = daily['precipitation_sum'][i]
                    emoji = code_meteo_vers_emoji(daily['weathercode'][i])
                    with streamlit.expander(f"{emoji} {d} — {tmin:.0f}°C / {tmax:.0f}°C", expanded=(i == 0)):
                        c1, c2, c3 = streamlit.columns(3)
                        c1.metric("🌡️ Max", f"{tmax:.1f}°C")
                        c2.metric("🌡️ Min", f"{tmin:.1f}°C")
                        c3.metric("🌧️ Précip.", f"{precip:.1f} mm")

                fig_temp = go.Figure()
                fig_temp.add_trace(go.Scatter(x=daily['time'][:5], y=daily['temperature_2m_max'][:5],
                    mode='lines+markers', name='Max', line=dict(color='#ef4444', width=2), marker=dict(size=8)))
                fig_temp.add_trace(go.Scatter(x=daily['time'][:5], y=daily['temperature_2m_min'][:5],
                    mode='lines+markers', name='Min', line=dict(color='#3b82f6', width=2), marker=dict(size=8)))
                fig_temp.update_layout(title=f"Températures — {ville}", xaxis_title="Date",
                    yaxis_title="°C", height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                streamlit.plotly_chart(fig_temp, use_container_width=True)
            else:
                streamlit.error("❌ Données météo indisponibles")

    streamlit.divider()
    streamlit.caption("📡 Données fournies par Open-Meteo.com")


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 5 : FORMATION
# ═══════════════════════════════════════════════════════════════════════════════

with onglet5:
    streamlit.header("Indicateurs Formation (Parcoursup)", divider="blue")

    col_commune = 'Commune de l\u2019établissement'
    if col_commune not in formations_data.columns:
        col_commune = "Commune de l'établissement"

    if col_commune in formations_data.columns:
        formations_A = formations_data[formations_data[col_commune].str.strip().str.lower() == ville_A.lower()]
        formations_B = formations_data[formations_data[col_commune].str.strip().str.lower() == ville_B.lower()]

        col_filiere = 'Filière de formation très agrégée'
        col_capacite = 'Capacité de l\u2019établissement par formation'
        if col_capacite not in formations_data.columns:
            col_capacite = "Capacité de l'établissement par formation"
        col_selectivite = 'Sélectivité'
        col_statut = 'Statut de l\u2019établissement de la filière de formation (public, privé…)'
        if col_statut not in formations_data.columns:
            col_statut = "Statut de l'établissement de la filière de formation (public, privé…)"

        filieres_dispos = list(set(
            formations_A[col_filiere].dropna().unique().tolist() +
            formations_B[col_filiere].dropna().unique().tolist()
        ))

        if filieres_dispos:
            st_filiere_filter = streamlit.multiselect("Filtrer par filière :", filieres_dispos, default=filieres_dispos)

            form_A_f = formations_A[formations_A[col_filiere].isin(st_filiere_filter)]
            form_B_f = formations_B[formations_B[col_filiere].isin(st_filiere_filter)]
            nb_A, nb_B = len(form_A_f), len(form_B_f)
            capa_A = pandas.to_numeric(form_A_f[col_capacite], errors='coerce').sum()
            capa_B = pandas.to_numeric(form_B_f[col_capacite], errors='coerce').sum()

            col1, col2 = streamlit.columns(2)
            with col1:
                streamlit.subheader(f"🔵 {ville_A}")
                m1, m2 = streamlit.columns(2)
                m1.metric("Formations", nb_A, delta=delta_str(nb_A, nb_B))
                m2.metric("Places totales", fmt(capa_A), delta=delta_str(capa_A, capa_B))
            with col2:
                streamlit.subheader(f"🟠 {ville_B}")
                m1, m2 = streamlit.columns(2)
                m1.metric("Formations", nb_B, delta=delta_str(nb_B, nb_A))
                m2.metric("Places totales", fmt(capa_B), delta=delta_str(capa_B, capa_A))

            streamlit.divider()

            fig_formation = make_subplots(rows=1, cols=3,
                subplot_titles=("Par filière", "Sélectivité", "Statut (Public/Privé)"))

            comptage_A = form_A_f[col_filiere].value_counts().reindex(st_filiere_filter, fill_value=0)
            comptage_B = form_B_f[col_filiere].value_counts().reindex(st_filiere_filter, fill_value=0)
            fig_formation.add_trace(go.Bar(name=ville_A, x=st_filiere_filter, y=comptage_A,
                marker_color=COULEUR_A, opacity=opacity_A, legendgroup='A'), row=1, col=1)
            fig_formation.add_trace(go.Bar(name=ville_B, x=st_filiere_filter, y=comptage_B,
                marker_color=COULEUR_B, opacity=opacity_B, legendgroup='B'), row=1, col=1)

            sel_A = form_A_f[col_selectivite].astype(str).value_counts()
            sel_B = form_B_f[col_selectivite].astype(str).value_counts()
            tous_sel = list(set([str(x) for x in sel_A.index.tolist() + sel_B.index.tolist()]))
            fig_formation.add_trace(go.Bar(name=ville_A, x=tous_sel, y=sel_A.reindex(tous_sel, fill_value=0),
                marker_color=COULEUR_A, opacity=opacity_A, legendgroup='A', showlegend=False), row=1, col=2)
            fig_formation.add_trace(go.Bar(name=ville_B, x=tous_sel, y=sel_B.reindex(tous_sel, fill_value=0),
                marker_color=COULEUR_B, opacity=opacity_B, legendgroup='B', showlegend=False), row=1, col=2)

            statut_A = form_A_f[col_statut].astype(str).value_counts()
            statut_B = form_B_f[col_statut].astype(str).value_counts()
            tous_statut = list(set([str(x) for x in statut_A.index.tolist() + statut_B.index.tolist()]))
            labels_courts = [s.replace("Privé sous contrat d'association", "Privé (Contrat)")
                              .replace("Privé hors contrat", "Privé (HC)")
                              .replace("Privé enseignement supérieur", "Privé (Sup)") for s in tous_statut]
            fig_formation.add_trace(go.Bar(name=ville_A, x=labels_courts, y=statut_A.reindex(tous_statut, fill_value=0),
                marker_color=COULEUR_A, opacity=opacity_A, legendgroup='A', showlegend=False), row=1, col=3)
            fig_formation.add_trace(go.Bar(name=ville_B, x=labels_courts, y=statut_B.reindex(tous_statut, fill_value=0),
                marker_color=COULEUR_B, opacity=opacity_B, legendgroup='B', showlegend=False), row=1, col=3)

            style_figure(fig_formation, 500)
            afficher_graphique(fig_formation, "chart_formation")
        else:
            streamlit.warning("Aucune donnée de formation pour ces villes.")
    else:
        streamlit.error("Colonne des communes introuvable dans le fichier Parcoursup.")


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 6 : SPORTS
# ═══════════════════════════════════════════════════════════════════════════════

def exploser_liste(df, col):
    """Explose une colonne contenant des listes et compte les valeurs."""
    if df.empty or col not in df.columns:
        return pandas.Series(dtype=int)
    series = df[col].dropna()
    toutes = []
    for val in series:
        if isinstance(val, list):
            toutes.extend([str(v).strip() for v in val])
        else:
            toutes.append(str(val).strip())
    counts = pandas.Series(toutes).value_counts()
    poubelle = {'nan', 'None', '', 'NaN', 'null', 'false', 'False', 'true', 'True'}
    return counts[~counts.index.isin(poubelle)]


with onglet6:
    streamlit.header("Indicateurs Sports", divider="blue")
    streamlit.info("🏟️ Données : Recensement des Équipements Sportifs (data.sports.gouv.fr)")

    with streamlit.spinner("Chargement des données sportives..."):
        sport_A = obtenir_equipements_sportifs(ville_A)
        sport_B = obtenir_equipements_sportifs(ville_B)

    col1, col2 = streamlit.columns(2)
    with col1:
        streamlit.subheader(f"🔵 {ville_A}")
        streamlit.metric("Équipements recensés", len(sport_A), delta=delta_str(len(sport_A), len(sport_B)))
    with col2:
        streamlit.subheader(f"🟠 {ville_B}")
        streamlit.metric("Équipements recensés", len(sport_B), delta=delta_str(len(sport_B), len(sport_A)))

    if not sport_A.empty or not sport_B.empty:
        streamlit.divider()
        streamlit.subheader("📊 Comparaison des équipements sportifs")

        count_A = sport_A['equip_type_name'].dropna().astype(str).value_counts().head(10) if not sport_A.empty and 'equip_type_name' in sport_A.columns else pandas.Series(dtype=int)
        count_B = sport_B['equip_type_name'].dropna().astype(str).value_counts().head(10) if not sport_B.empty and 'equip_type_name' in sport_B.columns else pandas.Series(dtype=int)
        all_types = list(dict.fromkeys(count_A.index.tolist() + count_B.index.tolist()))[:12]

        act_A = exploser_liste(sport_A, 'gen_2024fin_labellisation').head(10)
        act_B = exploser_liste(sport_B, 'gen_2024fin_labellisation').head(10)
        all_acts = list(dict.fromkeys(act_A.index.tolist() + act_B.index.tolist()))[:12]

        has_types = len(all_types) > 0
        has_acts = len(all_acts) > 0
        nb_cols = (1 if has_types else 0) + (1 if has_acts else 0)

        if nb_cols > 0:
            titles = []
            if has_types:
                titles.append("Types d'équipements")
            if has_acts:
                titles.append("Activités praticables")
            fig_sport = make_subplots(rows=1, cols=nb_cols, subplot_titles=titles)

            col_idx = 1
            if has_types:
                fig_sport.add_trace(go.Bar(name=ville_A, x=all_types,
                    y=[count_A.get(t, 0) for t in all_types],
                    marker_color=COULEUR_A, opacity=opacity_A, legendgroup='A'), row=1, col=col_idx)
                fig_sport.add_trace(go.Bar(name=ville_B, x=all_types,
                    y=[count_B.get(t, 0) for t in all_types],
                    marker_color=COULEUR_B, opacity=opacity_B, legendgroup='B'), row=1, col=col_idx)
                col_idx += 1

            if has_acts:
                fig_sport.add_trace(go.Bar(name=ville_A, x=all_acts,
                    y=[act_A.get(a, 0) for a in all_acts],
                    marker_color=COULEUR_A, opacity=opacity_A, legendgroup='A', showlegend=not has_types), row=1, col=col_idx)
                fig_sport.add_trace(go.Bar(name=ville_B, x=all_acts,
                    y=[act_B.get(a, 0) for a in all_acts],
                    marker_color=COULEUR_B, opacity=opacity_B, legendgroup='B', showlegend=not has_types), row=1, col=col_idx)

            style_figure(fig_sport, 500)
            afficher_graphique(fig_sport, "chart_sport")

        # Intérieur vs Extérieur
        if 'equip_nature' in (sport_A.columns.tolist() if not sport_A.empty else []) + (sport_B.columns.tolist() if not sport_B.empty else []):
            streamlit.divider()
            streamlit.subheader("🏠 Intérieur vs Extérieur")
            nature_A = sport_A['equip_nature'].dropna().astype(str).value_counts() if not sport_A.empty and 'equip_nature' in sport_A.columns else pandas.Series(dtype=int)
            nature_B = sport_B['equip_nature'].dropna().astype(str).value_counts() if not sport_B.empty and 'equip_nature' in sport_B.columns else pandas.Series(dtype=int)
            poubelle_nature = {'nan', 'None', '', 'NaN', 'null'}
            nature_A = nature_A[~nature_A.index.isin(poubelle_nature)]
            nature_B = nature_B[~nature_B.index.isin(poubelle_nature)]
            all_natures = list(dict.fromkeys(nature_A.index.tolist() + nature_B.index.tolist()))
            if all_natures:
                fig_nature = go.Figure()
                fig_nature.add_trace(go.Bar(name=ville_A, x=all_natures,
                    y=[nature_A.get(n, 0) for n in all_natures],
                    marker_color=COULEUR_A, opacity=opacity_A))
                fig_nature.add_trace(go.Bar(name=ville_B, x=all_natures,
                    y=[nature_B.get(n, 0) for n in all_natures],
                    marker_color=COULEUR_B, opacity=opacity_B))
                style_figure(fig_nature, 350)
                afficher_graphique(fig_nature, "chart_sport_nature")

        # Propriétaire des équipements
        if 'equip_prop_type' in (sport_A.columns.tolist() if not sport_A.empty else []) + (sport_B.columns.tolist() if not sport_B.empty else []):
            streamlit.divider()
            streamlit.subheader("🏛️ Propriétaire des équipements")
            prop_A = sport_A['equip_prop_type'].dropna().astype(str).value_counts() if not sport_A.empty and 'equip_prop_type' in sport_A.columns else pandas.Series(dtype=int)
            prop_B = sport_B['equip_prop_type'].dropna().astype(str).value_counts() if not sport_B.empty and 'equip_prop_type' in sport_B.columns else pandas.Series(dtype=int)
            prop_A = prop_A[~prop_A.index.isin({'nan', 'None', '', 'NaN', 'null'})]
            prop_B = prop_B[~prop_B.index.isin({'nan', 'None', '', 'NaN', 'null'})]
            all_props = list(dict.fromkeys(prop_A.index.tolist() + prop_B.index.tolist()))
            if all_props:
                fig_prop = go.Figure()
                fig_prop.add_trace(go.Bar(name=ville_A, x=all_props,
                    y=[prop_A.get(p, 0) for p in all_props],
                    marker_color=COULEUR_A, opacity=opacity_A))
                fig_prop.add_trace(go.Bar(name=ville_B, x=all_props,
                    y=[prop_B.get(p, 0) for p in all_props],
                    marker_color=COULEUR_B, opacity=opacity_B))
                style_figure(fig_prop, 350)
                afficher_graphique(fig_prop, "chart_sport_prop")
    else:
        streamlit.warning("Aucune donnée sportive trouvée pour ces villes via l'API.")


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 7 : TOURISME
# ═══════════════════════════════════════════════════════════════════════════════

with onglet7:
    streamlit.header("Indicateurs Tourisme", divider="blue")
    streamlit.info("🗺️ Données : OpenStreetMap via Overpass API (lieux touristiques dans un rayon de 10 km)")

    with streamlit.spinner("Chargement des données touristiques..."):
        tourisme_A = obtenir_lieux_touristiques(lat_A, lon_A)
        tourisme_B = obtenir_lieux_touristiques(lat_B, lon_B)

    col1, col2 = streamlit.columns(2)
    with col1:
        streamlit.subheader(f"🔵 {ville_A}")
        streamlit.metric("Sites touristiques", len(tourisme_A), delta=delta_str(len(tourisme_A), len(tourisme_B)))
    with col2:
        streamlit.subheader(f"🟠 {ville_B}")
        streamlit.metric("Sites touristiques", len(tourisme_B), delta=delta_str(len(tourisme_B), len(tourisme_A)))

    if not tourisme_A.empty or not tourisme_B.empty:
        streamlit.divider()
        streamlit.subheader("📊 Types de sites touristiques")

        types_A = tourisme_A['type'].map(lambda x: LABELS_TOURISME.get(x, x.title())).value_counts() if not tourisme_A.empty else pandas.Series(dtype=int)
        types_B = tourisme_B['type'].map(lambda x: LABELS_TOURISME.get(x, x.title())).value_counts() if not tourisme_B.empty else pandas.Series(dtype=int)
        all_types = list(dict.fromkeys([str(x) for x in types_A.index.tolist() + types_B.index.tolist()]))

        fig_tourisme = go.Figure()
        fig_tourisme.add_trace(go.Bar(name=ville_A, x=all_types,
            y=[types_A.get(t, 0) for t in all_types],
            marker_color=COULEUR_A, opacity=opacity_A))
        fig_tourisme.add_trace(go.Bar(name=ville_B, x=all_types,
            y=[types_B.get(t, 0) for t in all_types],
            marker_color=COULEUR_B, opacity=opacity_B))
        style_figure(fig_tourisme, 450)
        afficher_graphique(fig_tourisme, "chart_tourisme")

        # Carte des lieux touristiques
        streamlit.divider()
        streamlit.subheader("🗺️ Carte des sites touristiques")

        lieux_carte = []
        if not tourisme_A.empty:
            t_a = tourisme_A.copy()
            t_a['ville'] = ville_A
            lieux_carte.append(t_a)
        if not tourisme_B.empty:
            t_b = tourisme_B.copy()
            t_b['ville'] = ville_B
            lieux_carte.append(t_b)

        if lieux_carte:
            df_carte = pandas.concat(lieux_carte, ignore_index=True)
            df_carte['label'] = df_carte['type'].map(lambda x: LABELS_TOURISME.get(x, x.title()))

            fig_carte_t = px.scatter_mapbox(
                df_carte, lat='lat', lon='lon',
                hover_name='nom', hover_data={'lat': False, 'lon': False, 'label': True, 'ville': True},
                color='ville', color_discrete_map={ville_A: COULEUR_A, ville_B: COULEUR_B},
                zoom=6, height=500, mapbox_style='carto-positron'
            )
            fig_carte_t.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            streamlit.plotly_chart(fig_carte_t, use_container_width=True)

        # Liste des lieux
        streamlit.divider()
        streamlit.subheader("📋 Liste des sites")
        col1, col2 = streamlit.columns(2)
        with col1:
            if not tourisme_A.empty:
                for _, row in tourisme_A.head(15).iterrows():
                    label = LABELS_TOURISME.get(row['type'], row['type'].title())
                    streamlit.write(f"🔵 **{row['nom']}** — {label}")
            else:
                streamlit.caption("Aucun site trouvé")
        with col2:
            if not tourisme_B.empty:
                for _, row in tourisme_B.head(15).iterrows():
                    label = LABELS_TOURISME.get(row['type'], row['type'].title())
                    streamlit.write(f"🟠 **{row['nom']}** — {label}")
            else:
                streamlit.caption("Aucun site trouvé")
    else:
        streamlit.warning("Aucune donnée touristique trouvée pour ces villes via l'API.")


# ═══════════════════════════════════════════════════════════════════════════════
# ONGLET 8 : CLASSEMENT
# ═══════════════════════════════════════════════════════════════════════════════

with onglet8:
    streamlit.header("Classement parmi toutes les villes", divider="blue")
    streamlit.info(f"📊 Position de {ville_A} et {ville_B} parmi les {len(villes_data)} villes de + de 20 000 habitants")

    # Calculer les rangs pour chaque indicateur
    classements = {}
    nb_villes = len(villes_data)

    indicateurs_classement = {
        'Population': ('P22_POP', False),
        'Revenu médian': ('MED21', False),
        'Emplois': ('P22_EMPLT', False),
        'Logements': ('P22_LOG', False),
        'Ménages': ('P22_MEN', False),
    }

    # Taux calculés
    villes_data_calc = villes_data.copy()
    villes_data_calc['_taux_activite'] = (
        pandas.to_numeric(villes_data_calc['P22_ACT1564'], errors='coerce') /
        pandas.to_numeric(villes_data_calc['P22_POP1564'], errors='coerce') * 100
    )
    villes_data_calc['_taux_chomage'] = (
        pandas.to_numeric(villes_data_calc['P22_CHOM1564'], errors='coerce') /
        pandas.to_numeric(villes_data_calc['P22_ACT1564'], errors='coerce') * 100
    )
    villes_data_calc['_taux_vacance'] = (
        pandas.to_numeric(villes_data_calc['P22_LOGVAC'], errors='coerce') /
        pandas.to_numeric(villes_data_calc['P22_LOG'], errors='coerce') * 100
    )
    villes_data_calc['_densite'] = (
        pandas.to_numeric(villes_data_calc['P22_POP'], errors='coerce') /
        pandas.to_numeric(villes_data_calc['SUPERF'], errors='coerce')
    )

    indicateurs_classement['Taux d\'activité'] = ('_taux_activite', False)
    indicateurs_classement['Taux de chômage'] = ('_taux_chomage', True)  # inversé = moins c'est mieux
    indicateurs_classement['Taux de vacance'] = ('_taux_vacance', True)
    indicateurs_classement['Densité'] = ('_densite', False)

    resultats = []
    for nom_indic, (col_name, inverse) in indicateurs_classement.items():
        col_data = pandas.to_numeric(villes_data_calc[col_name], errors='coerce')
        rang_series = col_data.rank(ascending=inverse, method='min')

        idx_A = temp_A.index[0]
        idx_B = temp_B.index[0]
        rang_A = int(rang_series.loc[idx_A]) if idx_A in rang_series.index and not pandas.isna(rang_series.loc[idx_A]) else nb_villes
        rang_B = int(rang_series.loc[idx_B]) if idx_B in rang_series.index and not pandas.isna(rang_series.loc[idx_B]) else nb_villes

        val_A = col_data.loc[idx_A] if idx_A in col_data.index else 0
        val_B = col_data.loc[idx_B] if idx_B in col_data.index else 0

        resultats.append({
            'Indicateur': nom_indic,
            f'Rang {ville_A}': f"{rang_A}/{nb_villes}",
            f'Top % {ville_A}': f"{rang_A/nb_villes*100:.0f}%",
            f'Rang {ville_B}': f"{rang_B}/{nb_villes}",
            f'Top % {ville_B}': f"{rang_B/nb_villes*100:.0f}%",
            'Meilleur': ville_A if rang_A < rang_B else (ville_B if rang_B < rang_A else 'Égalité'),
        })

    df_classement = pandas.DataFrame(resultats)
    streamlit.dataframe(df_classement, use_container_width=True, hide_index=True)

    # Graphique des rangs
    streamlit.divider()
    streamlit.subheader("📊 Positionnement comparé")

    indic_names = [r['Indicateur'] for r in resultats]
    rangs_A = [int(r[f'Rang {ville_A}'].split('/')[0]) for r in resultats]
    rangs_B = [int(r[f'Rang {ville_B}'].split('/')[0]) for r in resultats]
    # Convertir en percentile (100 = meilleur)
    pct_A = [round((1 - r / nb_villes) * 100) for r in rangs_A]
    pct_B = [round((1 - r / nb_villes) * 100) for r in rangs_B]

    fig_rank = go.Figure()
    fig_rank.add_trace(go.Bar(name=ville_A, x=indic_names, y=pct_A,
        marker_color=COULEUR_A, opacity=opacity_A,
        text=[f"Top {100-p}%" for p in pct_A], textposition='auto'))
    fig_rank.add_trace(go.Bar(name=ville_B, x=indic_names, y=pct_B,
        marker_color=COULEUR_B, opacity=opacity_B,
        text=[f"Top {100-p}%" for p in pct_B], textposition='auto'))
    fig_rank.update_layout(
        yaxis_title="Percentile (100 = meilleur)",
        barmode='group', height=450,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif'), margin=dict(t=40, b=40),
    )
    fig_rank.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Médiane nationale")
    streamlit.plotly_chart(fig_rank, use_container_width=True)

    # Score global
    streamlit.divider()
    streamlit.subheader("🏅 Score global")
    score_A = round(sum(pct_A) / len(pct_A))
    score_B = round(sum(pct_B) / len(pct_B))
    c1, c2 = streamlit.columns(2)
    c1.metric(f"🔵 {ville_A}", f"{score_A}/100", delta=delta_str(score_A, score_B, " pts"))
    c2.metric(f"🟠 {ville_B}", f"{score_B}/100", delta=delta_str(score_B, score_A, " pts"))
