import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Suivi Santé - Houbad Med",
    page_icon="🩺",
    layout="wide"
)

# --- LOGIQUE BASE DE DONNÉES ---
def init_db():
    # Utilisation d'une nouvelle version de base de données pour assurer un tri propre
    conn = sqlite3.connect('suivi_houbad_v11.db')
    c = conn.cursor()
    # Table pour les mesures (incluant l'ID et les Notes)
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  systolique INTEGER, diastolique INTEGER, 
                  battements INTEGER, glycemie REAL, 
                  date_heure TEXT, notes TEXT)''')
    # Table pour les antécédents
    c.execute('''CREATE TABLE IF NOT EXISTS antecedents (id INTEGER PRIMARY KEY, texte TEXT)''')
    
    # Insertion automatique de tes anciennes valeurs si la table est vide
    c.execute("SELECT COUNT(*) FROM mesures")
    if c.fetchone()[0] == 0:
        anciennes_valeurs = [
             (175, 103, 56,0.0 , "2026-03-04 17:45", "Sans traitement zanidip; Vertige"),
            (150, 100, 0,  1.33, "2026-03-06 14:10", "vertige apres prière lors du marche"),
            (157, 107, 52, 0.0,  "2026-03-06 16:30", "Ancienne mesure"),
            (150, 100, 69, 0.0,  "2026-03-06 19:00", "avant iftar"),
            (154, 98,  0,  0.0,  "2026-03-06 19:52", "Ancienne mesure"),
            (138, 100, 68, 0.0,  "2026-03-06 20:30", "Apres iftar avec 1cp 10mg de zanidip")
            (151, 100, 73, 2.76,  "2026-03-06 20:30", "2 H Apres iftar avec 1cp 10mg de zanidip")
        ]
        c.executemany("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure, notes) VALUES (?, ?, ?, ?, ?, ?)", anciennes_valeurs)
    
    conn.commit()
    conn.close()

def ajouter_mesure(sys, dia, bpm, gly, dt, notes):
    conn = sqlite3.connect('suivi_houbad_v11.db')
    c = conn.cursor()
    # Formatage ISO pour un tri alphabétique/chronologique correct
    date_str = dt.strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure, notes) VALUES (?, ?, ?, ?, ?, ?)",
              (sys, dia, bpm, gly, date_str, notes))
    conn.commit()
    conn.close()

def charger_data():
    conn = sqlite3.connect('suivi_houbad_v11.db')
    # TRI CHRONOLOGIQUE : ASC (du plus ancien au plus récent)
    df = pd.read_sql_query("SELECT id, systolique, diastolique, battements, glycemie, date_heure, notes FROM mesures ORDER BY date_heure ASC", conn)
    ant = conn.cursor().execute("SELECT texte FROM antecedents WHERE id=1").fetchone()
    conn.close()
    return df, ant[0] if ant else ""

# Initialisation
init_db()
df_mesures, text_ant = charger_data()

# --- INTERFACE UTILISATEUR ---
st.title("🩺 Journal de Bord : Houbad Med")

# Section Antécédents
with st.expander("👨‍👩‍👧‍👦 Antécédents Familiaux", expanded=False):
    with st.form("form_ant"):
        nouveau_ant = st.text_area("Notes sur l'historique familial :", value=text_ant)
        if st.form_submit_button("Sauvegarder Antécédents"):
            conn = sqlite3.connect('suivi_houbad_v11.db')
            conn.cursor().execute("INSERT OR REPLACE INTO antecedents (id, texte) VALUES (1, ?)", (nouveau_ant,))
            conn.commit()
            conn.close()
            st.success("Enregistré avec succès !")
            st.rerun()

st.divider()

col_saisie, col_historique = st.columns([1, 2], gap="large")

with col_saisie:
    st.subheader("➕ Ajouter une Mesure")
    with st.form("form_saisie", clear_on_submit=True):
        d = st.date_input("Date", datetime.now())
        t = st.time_input("Heure (HH:MM)", datetime.now().time())
        
        c1, c2 = st.columns(2)
        with c1:
            s = st.number_input("SYS (Max)", 40, 250, 120)
            b = st.number_input("Pouls (BPM)", 0, 200, 70)
        with c2:
            di = st.number_input("DIA (Min)", 30, 150, 80)
            g = st.number_input("Glycémie (g/L)", 0.0, 5.0, 0.0, step=0.01)
        
        n = st.text_input("Observations / Notes")
        
        if st.form_submit_button("ENREGISTRER LA DONNÉE"):
            dt_comb = datetime.combine(d, t)
            ajouter_mesure(s, di, b, g, dt_comb, n)
            st.rerun()

with col_historique:
    st.subheader("📋 Historique Organisé par Heure")
    
    if not df_mesures.empty:
        # On prépare une copie pour l'affichage lisible
        df_display = df_mesures.copy()
        # Transformation de la date ISO (2026-03-06) vers format FR (06/03/2026)
        df_display['date_heure'] = df_display['date_heure'].apply(
            lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M").strftime("%d/%m/%Y %H:%M")
        )
        
        # Affichage du tableau
        st.dataframe(
            df_display.rename(columns={
                "id": "ID",
                "systolique": "SYS",
                "diastolique": "DIA",
                "battements": "Pouls",
                "glycemie": "Glycémie",
                "date_heure": "Date/Heure",
                "notes": "Observations"
            }), 
            use_container_width=True,
            hide_index=True
        )

        # Zone de suppression
        with st.expander("🗑️ Supprimer une erreur"):
            to_del = st.number_input("Entrez l'ID de la ligne à effacer", min_value=1, step=1)
            if st.button("Confirmer Suppression"):
                conn = sqlite3.connect('suivi_houbad_v11.db')
                conn.cursor().execute("DELETE FROM mesures WHERE id = ?", (to_del,))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.info("Aucune donnée enregistrée pour le moment.")

st.markdown("---")
st.caption("Application de suivi médical privée - Houbad Med")
st.divider()
st.markdown("<h3 style='text-align: center; color: grey;'>Élaboré par Houbad Douaa</h3>", unsafe_allow_html=True)
