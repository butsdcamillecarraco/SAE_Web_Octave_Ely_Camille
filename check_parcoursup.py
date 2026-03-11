import pandas
df = pandas.read_csv('base_formation_parcoursup.csv', sep=';', low_memory=False)
col_commune = [c for c in df.columns if 'ommune' in c][0]
print("Col commune:", repr(col_commune))
niort = df[df[col_commune].str.strip().str.lower() == 'niort']
lorient = df[df[col_commune].str.strip().str.lower() == 'lorient']
print('Niort formations:', len(niort))
print('Lorient formations:', len(lorient))
print('Sample communes:', df[col_commune].dropna().unique()[:20])
col_filiere = [c for c in df.columns if 'très agrégée' in c.lower()][0] if any('très agrégée' in c.lower() for c in df.columns) else None
print('Col filiere:', repr(col_filiere))
if col_filiere:
    print('Filières:', df[col_filiere].unique())
col_sel = [c for c in df.columns if 'lectivit' in c.lower()][0] if any('lectivit' in c.lower() for c in df.columns) else None
print('Col selectivite:', repr(col_sel))
if col_sel:
    print('Sélectivité:', df[col_sel].unique())
col_statut = [c for c in df.columns if 'public' in c.lower()][0] if any('public' in c.lower() for c in df.columns) else None
print('Col statut:', repr(col_statut))
if col_statut:
    print('Statut:', df[col_statut].unique())
