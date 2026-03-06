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
    # Passage à la version v15 pour inclure la table des traitements
    conn = sqlite3.connect('suivi_houbad_v15.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  systolique INTEGER, diastolique INTEGER, 
                  battements INTEGER, glycemie REAL, 
                  date_heure TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS antecedents (id INTEGER PRIMARY KEY, texte TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS traitements (id INTEGER PRIMARY KEY, texte TEXT)''')
    
    # Insertion des antécédents si la table est vide
    c.execute("SELECT COUNT(*) FROM antecedents")
    if c.fetchone()[0] == 0:
        notes_medicales = "HTA, Diabète non insulinodépendant, Polykystose hépatorénale, Goutte"
        c.execute("INSERT INTO antecedents (id, texte) VALUES (1, ?)", (notes_medicales,))

    # Insertion automatique des anciennes valeurs
    c.execute("SELECT COUNT(*) FROM mesures")
    if c.fetchone()[0] == 0:
        anciennes_valeurs = [
            (175, 103, 56, 0.0,  "2026-03-04 17:45", "Sans traitement zanidip; Vertige"),
            (150, 100, 0,  1.33, "2026-03-06 14:10", "vertige apres prière lors du marche"),
            (157, 107, 52, 0.0,  "2026-03-06 16:30", "Ancienne mesure"),
            (150, 100, 69, 0.0,  "2026-03-06 19:00", "avant iftar"),
            (154, 98,  0,  0.0,  "2026-03-06 19:52", "Ancienne mesure"),
            (138, 100, 68, 0.0,  "2026-03-06 20:30", "Apres iftar avec 1cp 10mg de zanidip"),
            (133, 90, 71, 2.76, "2026-03-06 22:20", "2 H Apres iftar avec 1cp 10mg de zanidip")
        ]
        c.executemany("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure, notes) VALUES (?, ?, ?, ?, ?, ?)", anciennes_valeurs)
    
    conn.commit()
    conn.close()

def charger_data():
    conn = sqlite3.connect('suivi_houbad_v15.db')
    df = pd.read_sql_query("SELECT id, systolique, diastolique, battements, glycemie, date_heure, notes FROM mesures ORDER BY date_heure ASC", conn)
    ant = conn.cursor().execute("SELECT texte FROM antecedents WHERE id=1").fetchone()
    traite = conn.cursor().execute("SELECT texte FROM traitements WHERE id=1").fetchone()
    conn.close()
    return df, ant[0] if ant else "", traite[0] if traite else ""

# Initialisation
init_db()
df_mesures, text_ant, text_traite = charger_data()

# --- INTERFACE UTILISATEUR ---
st.title("🩺 Journal de Bord : Houbad Med")

# Colonnes pour Antécédents et Traitement
col_med1, col_med2 = st.columns(2)

with col_med1:
    with st.expander("👨‍👩‍👧‍👦 Antécédents Médicaux", expanded=False):
        with st.form("form_ant"):
            nouveau_ant = st.text_area("Historique :", value=text_ant, height=100)
            if st.form_submit_button("Sauvegarder Antécédents"):
                conn = sqlite3.connect('suivi_houbad_v15.db')
                conn.cursor().execute("INSERT OR REPLACE INTO埋 antecedents (id, texte) VALUES (1, ?)", (nouveau_ant,))
                conn.commit()
                conn.close()
                st.rerun()

with col_med2:
    with st.expander("💊 Traitement Actuel", expanded=True):
        with st.form("form_traite"):
            nouveau_traite = st.text_area("Médicaments et grammages :", value=text_traite, height=100, placeholder="Ex: Zanidip 10mg, 1cp le soir")
            if st.form_submit_button("Sauvegarder Traitement"):
                conn = sqlite3.connect('suivi_houbad_v15.db')
                conn.cursor().execute("INSERT OR REPLACE INTO traitements (id, texte) VALUES (1, ?)", (nouveau_traite,))
                conn.commit()
                conn.close()
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
            conn = sqlite3.connect('suivi_houbad_v15.db')
            date_str = dt_comb.strftime("%Y-%m-%d %H:%M")
            conn.cursor().execute("INSERT INTO埋 mesures (systolique, diastolique, battements, glycemie, date_heure, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                  (s, di, b, g, date_str, n))
            conn.commit()
            conn.close()
            st.rerun()

with col_historique:
    st.subheader("📋 Historique Organisé par Heure")
    
    if not df_mesures.empty:
        df_display = df_mesures.copy()
        df_display['date_heure'] = df_display['date_heure'].apply(
            lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M").strftime("%d/%m/%Y %H:%M")
        )
        
        st.dataframe(
            df_display.rename(columns={
                "id": "ID", "systolique": "SYS", "diastolique": "DIA", 
                "battements": "Pouls", "glycemie": "Glycémie", 
                "date_heure": "Date/Heure", "notes": "Observations"
            }), 
            use_container_width=True,
            hide_index=True
        )

        with st.expander("🗑️ Supprimer une erreur"):
            to_del = st.number_input("Entrez l'ID de la ligne", min_value=1, step=1)
            if st.button("Confirmer Suppression"):
                conn = sqlite3.connect('suivi_houbad_v15.db')
                conn.cursor().execute("DELETE FROM埋 mesures WHERE id = ?", (to_del,))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.info("Aucune donnée enregistrée.")

st.markdown("---")
st.caption("Application de suivi médical privée - Houbad Med")
st.divider()
st.markdown("<h3 style='text-align: center; color: grey;'>Élaboré par Houbad Douaa</h3>", unsafe_allow_html=True)
