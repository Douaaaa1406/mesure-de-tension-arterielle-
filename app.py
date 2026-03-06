import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuration de base robuste
st.set_page_config(page_title="Suivi Houbad Med", layout="wide")

# Initialisation de la base de données
def init_db():
    conn = sqlite3.connect('suivi_houbad_v6.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  systolique INTEGER, diastolique INTEGER, 
                  battements INTEGER, glycemie REAL, 
                  date_heure TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS antecedents (id INTEGER PRIMARY KEY, texte TEXT)''')
    conn.commit()
    conn.close()

def ajouter_mesure(sys, dia, bpm, gly, dt, notes):
    conn = sqlite3.connect('suivi_houbad_v6.db')
    c = conn.cursor()
    # Formatage de la date et l'heure en HH:MM précisément
    date_str = dt.strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure, notes) VALUES (?, ?, ?, ?, ?, ?)",
              (sys, dia, bpm, gly, date_str, notes))
    conn.commit()
    conn.close()

def charger_data():
    conn = sqlite3.connect('suivi_houbad_v6.db')
    # Tri par date et heure décroissante
    df = pd.read_sql_query("SELECT * FROM mesures ORDER BY date_heure DESC", conn)
    ant = conn.cursor().execute("SELECT texte FROM antecedents WHERE id=1").fetchone()
    conn.close()
    return df, ant[0] if ant else ""

init_db()
df_mesures, text_ant = charger_data()

# --- INTERFACE ---
st.title("🩺 Suivi Patient : Houbad Med")

# Section Antécédents
with st.expander("👨‍👩‍👧‍👦 Antécédents Familiaux", expanded=False):
    with st.form("form_ant"):
        nouveau_ant = st.text_area("Notes sur l'historique familial :", value=text_ant)
        if st.form_submit_button("Sauvegarder Antécédents"):
            conn = sqlite3.connect('suivi_houbad_v6.db')
            conn.cursor().execute("INSERT OR REPLACE INTO antecedents (id, texte) VALUES (1, ?)", (nouveau_ant,))
            conn.commit()
            conn.close()
            st.rerun()

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ Nouvelle Saisie")
    with st.form("form_saisie", clear_on_submit=True):
        st.write("### Date et Heure Précise")
        d = st.date_input("Choisir le jour", datetime.now())
        # L'entrée d'heure permet de choisir précisément HH:MM
        t = st.time_input("Choisir l'heure (HH:MM)", datetime.now().time())
        
        st.write("### Valeurs Médicales")
        c1, c2 = st.columns(2)
        with c1:
            s = st.number_input("Tension SYS", 40, 250, 120)
            b = st.number_input("Pouls (BPM)", 30, 200, 70)
        with c2:
            di = st.number_input("Tension DIA", 30, 150, 80)
            g = st.number_input("Glycémie (g/L)", 0.0, 5.0, 1.0, step=0.01)
        
        n = st.text_input("Observations / Notes (facultatif)")
        
        if st.form_submit_button("ENREGISTRER LA MESURE"):
            dt_comb = datetime.combine(d, t)
            ajouter_mesure(s, di, b, g, dt_comb, n)
            st.rerun()

with col2:
    st.subheader("📊 Historique Chronologique")
    if not df_mesures.empty:
        # Petit résumé rapide de la dernière saisie
        last = df_mesures.iloc[0]
        # On reformate l'affichage de la date pour l'utilisateur en JJ/MM/AAAA HH:MM
        try:
            date_obj = datetime.strptime(last['date_heure'], "%Y-%m-%d %H:%M")
            date_affichée = date_obj.strftime("%d/%m/%Y à %H:%M")
        except:
            date_affichée = last['date_heure']

        st.info(f"Dernière mesure : **{date_affichée}** | Tension: **{int(last['systolique'])}/{int(last['diastolique'])}** | Glycémie: **{last['glycemie']}**")
        
        # Préparation du tableau pour l'affichage
        df_display = df_mesures.copy()
        # Conversion du format de date interne (YYYY-MM-DD HH:MM) vers un format lisible (DD/MM/YYYY HH:MM)
        df_display['date_heure'] = df_display['date_heure'].apply(
            lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M").strftime("%d/%m/%Y %H:%M")
        )
        
        df_display = df_display.drop(columns=['id']).rename(columns={
            "systolique": "SYS",
            "diastolique": "DIA",
            "battements": "Pouls",
            "glycemie": "Glycémie",
            "date_heure": "Date & Heure (HH:MM)",
            "notes": "Observations"
        })
        
        st.dataframe(df_display, use_container_width=True)

        # Suppression
        with st.expander("🗑️ Supprimer une ligne"):
            to_del = st.selectbox("Sélectionner l'heure de la mesure à effacer", 
                                  options=df_mesures['id'].tolist(),
                                  format_func=lambda x: df_mesures.loc[df_mesures['id']==x, 'date_heure'].values[0])
            if st.button("Confirmer la suppression"):
                conn = sqlite3.connect('suivi_houbad_v6.db')
                conn.cursor().execute("DELETE FROM mesures WHERE id = ?", (to_del,))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.write("Le journal est vide.")
