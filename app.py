import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuration de base (sans fioritures pour éviter les erreurs)
st.set_page_config(page_title="Suivi Houbad Med", layout="wide")

# Initialisation de la base de données
def init_db():
    conn = sqlite3.connect('suivi_houbad_v5.db')
    c = conn.cursor()
    # Ajout de la colonne 'notes' dans la table mesures
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  systolique INTEGER, diastolique INTEGER, 
                  battements INTEGER, glycemie REAL, 
                  date_heure TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS antecedents (id INTEGER PRIMARY KEY, texte TEXT)''')
    conn.commit()
    conn.close()

def ajouter_mesure(sys, dia, bpm, gly, dt, notes):
    conn = sqlite3.connect('suivi_houbad_v5.db')
    c = conn.cursor()
    date_str = dt.strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure, notes) VALUES (?, ?, ?, ?, ?, ?)",
              (sys, dia, bpm, gly, date_str, notes))
    conn.commit()
    conn.close()

def charger_data():
    conn = sqlite3.connect('suivi_houbad_v5.db')
    df = pd.read_sql_query("SELECT * FROM mesures ORDER BY date_heure DESC", conn)
    ant = conn.cursor().execute("SELECT texte FROM antecedents WHERE id=1").fetchone()
    conn.close()
    return df, ant[0] if ant else ""

init_db()
df_mesures, text_ant = charger_data()

# --- INTERFACE ---
st.title("🩺 Suivi Patient : Houbad Med")

# Section Antécédents (Toujours visible en haut)
with st.expander("👨‍👩‍👧‍👦 Antécédents Familiaux (Cliquez pour modifier)", expanded=False):
    with st.form("form_ant"):
        nouveau_ant = st.text_area("Notes sur l'historique familial :", value=text_ant)
        if st.form_submit_button("Sauvegarder Antécédents"):
            conn = sqlite3.connect('suivi_houbad_v5.db')
            conn.cursor().execute("INSERT OR REPLACE INTO antecedents (id, texte) VALUES (1, ?)", (nouveau_ant,))
            conn.commit()
            conn.close()
            st.rerun()

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ Nouvelle Saisie")
    with st.form("form_saisie", clear_on_submit=True):
        st.write("### Date et Heure")
        d = st.date_input("Date de la mesure", datetime.now())
        t = st.time_input("Heure de la mesure", datetime.now().time())
        
        st.write("### Valeurs")
        c1, c2 = st.columns(2)
        with c1:
            s = st.number_input("SYS", 40, 250, 120)
            b = st.number_input("Pouls", 30, 200, 70)
        with c2:
            di = st.number_input("DIA", 30, 150, 80)
            g = st.number_input("Glycémie", 0.0, 5.0, 1.0, step=0.01)
        
        # AJOUT DE LA CASE NOTES
        n = st.text_input("Notes / Observations (ex: après manger, fatigue...)")
        
        if st.form_submit_button("ENREGISTRER"):
            dt_comb = datetime.combine(d, t)
            ajouter_mesure(s, di, b, g, dt_comb, n)
            st.rerun()

with col2:
    st.subheader("📊 Historique des Mesures")
    if not df_mesures.empty:
        # Affichage du dernier relevé
        last = df_mesures.iloc[0]
        st.info(f"Dernier relevé le {last['date_heure']} : {int(last['systolique'])}/{int(last['diastolique'])} mmHg, {last['glycemie']} g/L")
        
        # On affiche le tableau
        # On renomme pour que ce soit plus joli
        df_display = df_mesures.drop(columns=['id']).rename(columns={
            "systolique": "SYS",
            "diastolique": "DIA",
            "battements": "Pouls",
            "glycemie": "Glycémie",
            "date_heure": "Date/Heure",
            "notes": "Observations"
        })
        st.dataframe(df_display, use_container_width=True)

        # Bouton de suppression simplifié
        with st.expander("🗑️ Supprimer une ligne"):
            to_del = st.selectbox("Choisir la ligne à effacer", options=df_mesures['id'].tolist(),
                                  format_func=lambda x: df_mesures.loc[df_mesures['id']==x, 'date_heure'].values[0])
            if st.button("Confirmer la suppression"):
                conn = sqlite3.connect('suivi_houbad_v5.db')
                conn.cursor().execute("DELETE FROM mesures WHERE id = ?", (to_del,))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.write("Aucune donnée enregistrée.")
