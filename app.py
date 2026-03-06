import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuration de base robuste
st.set_page_config(page_title="Suivi Santé - Houbad Med", layout="wide")

# Initialisation de la base de données
def init_db():
    conn = sqlite3.connect('suivi_houbad_v9.db') # Nouvelle version pour repartir propre
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  systolique INTEGER, diastolique INTEGER, 
                  battements INTEGER, glycemie REAL, 
                  date_heure TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS antecedents (id INTEGER PRIMARY KEY, texte TEXT)''')
    
    # Vérification et insertion des données historiques
    c.execute("SELECT COUNT(*) FROM mesures")
    if c.fetchone()[0] == 0:
        anciennes_valeurs = [
            (150, 100, 0,  1.33, "2026-03-06 14:10", "vertige apres prière lors du marche"),
            (157, 107, 52, 0.0,  "2026-03-06 16:30", "Ancienne mesure"),
            (150, 100, 69, 0.0,  "2026-03-06 19:00", "avant iftar"),
            (154, 98,  0,  0.0,  "2026-03-06 19:52", "Ancienne mesure"),
            (138, 100, 68, 0.0,  "2026-03-06 20:30", "Apres iftar avec 1cp 10mg de zanidip")
        ]
        c.executemany("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure, notes) VALUES (?, ?, ?, ?, ?, ?)", anciennes_valeurs)
    
    conn.commit()
    conn.close()

def ajouter_mesure(sys, dia, bpm, gly, dt, notes):
    conn = sqlite3.connect('suivi_houbad_v9.db')
    c = conn.cursor()
    date_str = dt.strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure, notes) VALUES (?, ?, ?, ?, ?, ?)",
              (sys, dia, bpm, gly, date_str, notes))
    conn.commit()
    conn.close()

def charger_data():
    conn = sqlite3.connect('suivi_houbad_v9.db')
    df = pd.read_sql_query("SELECT id, systolique, diastolique, battements, glycemie, date_heure, notes FROM mesures ORDER BY date_heure DESC", conn)
    ant = conn.cursor().execute("SELECT texte FROM antecedents WHERE id=1").fetchone()
    conn.close()
    return df, ant[0] if ant else ""

init_db()
df_mesures, text_ant = charger_data()

# --- INTERFACE ---
st.title("🩺 Journal de Bord : Houbad Med")

with st.expander("👨‍👩‍👧‍👦 Antécédents Familiaux", expanded=False):
    with st.form("form_ant"):
        nouveau_ant = st.text_area("Notes sur l'historique familial :", value=text_ant)
        if st.form_submit_button("Sauvegarder"):
            conn = sqlite3.connect('suivi_houbad_v9.db')
            conn.cursor().execute("INSERT OR REPLACE INTO antecedents (id, texte) VALUES (1, ?)", (nouveau_ant,))
            conn.commit()
            conn.close()
            st.rerun()

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ Ajouter une Mesure")
    with st.form("form_saisie", clear_on_submit=True):
        d = st.date_input("Date", datetime.now())
        t = st.time_input("Heure (HH:MM)", datetime.now().time())
        c1, c2 = st.columns(2)
        with c1:
            s = st.number_input("SYS (Tension Max)", 40, 250, 120)
            b = st.number_input("Pouls (BPM)", 0, 200, 70)
        with c2:
            di = st.number_input("DIA (Tension Min)", 30, 150, 80)
            g = st.number_input("Glycémie (g/L)", 0.0, 5.0, 0.0, step=0.01)
        
        n = st.text_input("Notes / Observations")
        if st.form_submit_button("ENREGISTRER"):
            dt_comb = datetime.combine(d, t)
            ajouter_mesure(s, di, b, g, dt_comb, n)
            st.rerun()

with col2:
    st.subheader("📋 Historique des Mesures")
    
    if not df_mesures.empty:
        df_display = df_mesures.copy()
        # Formatage de la date pour l'affichage
        df_display['date_heure'] = df_display['date_heure'].apply(
            lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M").strftime("%d/%m/%Y %H:%M")
        )
        
        st.dataframe(df_display.rename(columns={
            "id": "ID",
            "systolique": "SYS",
            "diastolique": "DIA",
            "battements": "Pouls",
            "glycemie": "Glycémie",
            "date_heure": "Date/Heure",
            "notes": "Observations"
        }), use_container_width=True)

        with st.expander("🗑️ Supprimer une ligne"):
            to_del = st.number_input("Entrez l'ID à supprimer", min_value=1, step=1)
            if st.button("Confirmer Suppression"):
                conn = sqlite3.connect('suivi_houbad_v9.db')
                conn.cursor().execute("DELETE FROM mesures WHERE id = ?", (to_del,))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.write("Aucune donnée enregistrée.")
