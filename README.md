# Comparateur de Villes Françaises

**Projet noté - BUT SD2 VCOD - Programmation Web**  
**Technologie:** Streamlit  
**Date:** Mars 2026

---

## 📋 Description

Application web interactive permettant de comparer deux villes françaises de plus de 20 000 habitants selon plusieurs critères :

- 📍 **Généralités & Cartographie** : Population, superficie, densité, revenu médian, localisation GPS
- 💼 **Emploi** : Taux d'activité, taux de chômage, répartition des emplois
- 🏠 **Logement** : Types de logements, taux de vacance, propriétaires/locataires
- 🌤️ **Météo** : Prévisions météorologiques sur 5 jours (données en temps réel)

- 🎓 **Formation** : 
- 🏅 **Sports** : 
- 🎭 **Culture** : 
- 🧭 **Tourisme** : 

---

## 🎯 Fonctionnalités

### ✅ Exigences du sujet respectées

- [x] Comparaison de 2 villes françaises (> 20 000 habitants)
- [x] Interface Streamlit avec plusieurs onglets
- [x] Données générales (population, superficie, revenu)
- [x] Indicateurs Emploi (taux activité/chômage, emplois)
- [x] Indicateurs Logement (répartition, vacance, propriétaires)
- [x] Météo (prévisions 5 jours via API Open-Meteo)
- [x] Cartographie interactive des villes

### 🎨 Points forts

- Interface moderne et intuitive
- Graphiques interactifs (Plotly)
- Données en temps réel (API météo)
- Code commenté et structuré
- Villes par défaut : **Niort** et **Lorient**

---

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- `pip` (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner ou télécharger le projet**
   ```bash
   cd projet_js
   ```

2. **Créer un environnement virtuel** (recommandé)
   ```bash
   python -m venv .venv
   ```

3. **Activer l'environnement virtuel**
   - Windows :
     ```bash
     .venv\Scripts\activate
     ```
   - macOS/Linux :
     ```bash
     source .venv/bin/activate
     ```

4. **Installer les dépendances**
   ```bash
   pip install streamlit pandas plotly requests pypdf
   ```

---

## ▶️ Lancement de l'application

1. **Lancer Streamlit**
   ```bash
   streamlit run app.py
   ```

2. **Accéder à l'interface**
   - L'application s'ouvrira automatiquement dans votre navigateur
   - Sinon, accédez manuellement à : **http://localhost:8501**

---

## 📂 Structure du projet

```
projet_js/
│
├── app.py                                    # Application principale Streamlit
├── base_cc_comparateur.csv                   # Données INSEE (indicateurs socio-économiques)
├── 20230823-communes-departement-region.csv  # Données géographiques (GPS, noms)
├── 0-SujetProjet.pdf                         # Énoncé du projet
├── README.md                                 # Ce fichier
└── .venv/                                    # Environnement virtuel (si créé)
```

---

## 📊 Sources de données

| Donnée | Source | Format |
|--------|--------|--------|
| Indicateurs socio-économiques | INSEE (base communale) | CSV |
| Coordonnées GPS | Data.gouv.fr | CSV |
| Prévisions météo | Open-Meteo API (gratuite) | JSON (REST API) |

---

## 🎯 Utilisation

1. **Sélectionner les villes** dans la barre latérale gauche
2. **Naviguer entre les onglets** pour explorer les différents indicateurs
3. **Interagir avec les graphiques** (zoom, survol, téléchargement)

### Exemple de comparaison par défaut
- **Ville A** : Niort (79, Deux-Sèvres)
- **Ville B** : Lorient (56, Morbihan)

---

## 🛠️ Technologies utilisées

- **Streamlit** : Framework web Python
- **Pandas** : Manipulation de données
- **Plotly** : Graphiques interactifs
- **Requests** : Appels API météo
- **Open-Meteo API** : Données météorologiques

---

## 📝 Notes techniques

### Code optimisé
- Mise en cache des données (`@streamlit.cache_data`) pour performances
- Normalisation des codes communes (format 5 caractères)
- Suppression des doublons
- Gestion d'erreurs pour l'API météo

### Respect des contraintes
- Filtre automatique : communes > 20 000 habitants
- Fusion propre des sources de données (INSEE + géo)
- Code commenté pour faciliter la compréhension
- Architecture modulaire (fonctions dédiées)

---

## 👥 Auteurs

**Groupe Streamlit**  
Projet BUT SD2 VCOD - Mars 2026

---

## 📧 Support

En cas de problème :
1. Vérifier que toutes les dépendances sont installées
2. Vérifier que les fichiers CSV sont présents dans le dossier
3. Vérifier que le port 8501 n'est pas déjà utilisé

---

## 📜 Licence

Projet académique - BUT SD2 VCOD 2026
