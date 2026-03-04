# Copilot instructions for this repository

## Project snapshot
- This is a **complete Streamlit application** in `app.py` for comparing French cities (> 20,000 inhabitants).
- **4 functional tabs**: Généralités & Carte, Emploi, Logement, Météo
- Runtime data comes from two CSV files at repo root:
  - `base_cc_comparateur.csv` (INSEE socio-economic indicators)
  - `20230823-communes-departement-region.csv` (geographic metadata)
- Weather data is fetched in real-time from **Open-Meteo API** (free, no API key)
- Default cities: **Niort** and **Lorient**

## Architecture and data flow
1. `charger_donnees()` loads both CSV files with `pandas.read_csv`.
2. Join keys are normalized to 5-char strings via `.astype(str).str.zfill(5)` (`CODGEO` / `code_commune_INSEE`).
3. Business filter is applied early with `.query("P22_POP > 20000")` (project requirement).
4. Dataframes are merged with `pandas.merge(..., how="inner")`.
5. Duplicate communes are removed with `.drop_duplicates(subset=['CODGEO'])`.
6. Final dataset is sorted by `nom_commune_complet`, then used for UI selections and plots.
7. `obtenir_meteo()` fetches 5-day weather forecasts from Open-Meteo API with 1h cache.

Why this structure matters:
- The merge/normalization step is the core correctness boundary.
- `@streamlit.cache_data` on `charger_donnees()` is intentional for performance; preserve it.
- Weather cache (ttl=3600) avoids API rate limits; respect this pattern.

## UI/component conventions
- Layout style: `streamlit.set_page_config(..., layout="wide")`, sidebar selectors, **4 tabs**
- French naming throughout (`ville_A`, `ville_B`, `onglet1-4`, etc.); stay consistent
- Map uses `plotly.express.scatter_mapbox` with `mapbox_style="carto-positron"`
- Colors: ville_A = blue (#1f77b4), ville_B = green (#2ca02c)
- All numbers formatted with French separators (space for thousands)

## Key indicators by tab
**Tab 1 - Généralités:**
- Population, superficie, densité, ménages, revenu médian
- Interactive mapbox with both cities

**Tab 2 - Emploi:**
- Taux d'activité, taux de chômage, emplois totaux
- Charts: population répartition, taux comparés, emplois salariés/non-salariés
- Uses columns: `P22_POP1564`, `P22_ACT1564`, `P22_CHOM1564`, `P22_EMPLT`, `P22_EMPLT_SAL`

**Tab 3 - Logement:**
- Logements totaux, taux vacance, taux propriétaires
- Charts: répartition (RP/RS/vacants), statut occupation (pie charts), taux comparés
- Uses columns: `P22_LOG`, `P22_RP`, `P22_RSECOCC`, `P22_LOGVAC`, `P22_RP_PROP`

**Tab 4 - Météo:**
- 5-day forecast with Open-Meteo API
- Temperature evolution line charts
- Weather code to emoji conversion

## Agent workflow expectations
- Launch locally with: `streamlit run app.py`
- Dependencies: `pip install streamlit pandas plotly requests`
- App runs on http://localhost:8501 (or 8502 if port occupied)
- Validate changes by checking:
  - All 4 tabs load without errors
  - City selectors populate with cities > 20k inhabitants
  - Map renders both cities correctly
  - Charts display properly in Emploi and Logement tabs
  - Weather API calls succeed (or fail gracefully with error message)

## Change guidelines specific to this repo
- Preserve `.query(...)` and dataframe-centric style
- When adding indicators/charts, derive city data from `temp_A` / `temp_B` pattern
- Always check if column exists in CSV before using it
- Respect French formatting (spaces for thousands, commas for decimals when needed)
- Maintain consistent color scheme (blue/green) across all visualizations
- For new API calls, add caching with appropriate TTL
- Keep docstrings updated (they're used for QCM evaluation)

## Project requirements (sujet)
- Cities filter: `> 20,000 inhabitants` (mandatory)
- Required data: Généralités, Emploi, Logement, Météo
- Required feature: Interactive map of all cities
- Evaluation criteria: code comments, clean architecture, no dead code, professional README
- Delivery: compressed archive with all files

## Key files to read first
- `app.py` (all app logic and UI flow - ~700 lines, well-commented)
- `README.md` (installation and usage instructions)
- `base_cc_comparateur.csv` (32 columns of INSEE indicators)
- `20230823-communes-departement-region.csv` (location and commune naming columns)
