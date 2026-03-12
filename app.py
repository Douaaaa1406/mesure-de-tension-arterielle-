import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Suivi Santé - Houbad Med", page_icon="🩺", layout="wide")

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('sante_houbad_v3.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY, 
                  sys INTEGER, dia INTEGER, pouls INTEGER, 
                  glycemie REAL, date_heure TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS infos (type TEXT PRIMARY KEY, contenu TEXT)''')
    
    # --- VOS MESURES FOURNIES (Données de base permanentes) ---
    mesures_historiques = [
        (1, 175, 103, 56, 0.0, "04/03/2026 17:45", "Sans traitement; Vertige"),
        (2, 150, 100, 0,  1.33, "06/03/2026 14:10", "vertige apres prière"),
        (3, 157, 107, 52, 0.0,  "06/03/2026 16:30", "Ancienne mesure"),
        (4, 150, 100, 69, 0.0,  "06/03/2026 19:00", "avant iftar"),
        (5, 154, 98,  0,  0.0,  "06/03/2026 19:52", "Ancienne mesure"),
        (6, 138, 100, 68, 0.0,  "06/03/2026 20:30", "Apres iftar (Zanidip)"),
        (7, 133, 90,  71, 2.76, "06/03/2026 21:25", "2H après Iftar"),
        (8, 135, 86,  63, 0.0,  "07/03/2026 04:56", "Shor"),
        (9, 113, 85,  70, 2.29, "11/03/2026 21:00", "zanidip a la priere")
    ]
    
    # Insertion automatique si la ligne n'existe pas
    for m in mesures_historiques:
        c.execute("INSERT OR IGNORE INTO mesures VALUES (?,?,?,?,?,?,?)", m)
    
    c.execute("INSERT OR IGNORE INTO infos VALUES ('ant', '')")
    c.execute("INSERT OR IGNORE INTO infos VALUES ('traite', '')")
    conn.commit()
    return conn

# Connexion stable
conn = init_db()

# --- RÉCUPÉRATION ---
def charger_data():
    df = pd.read_sql_query("SELECT * FROM mesures ORDER BY id DESC", conn)
    ant = conn.execute("SELECT contenu FROM infos WHERE type='ant'").fetchone()[0]
    traite = conn.execute("SELECT contenu FROM infos WHERE type='traite'").fetchone()[0]
    return df, ant, traite

df_mesures, text_ant, text_traite = charger_data()

st.title("🩺 Journal de Bord : Houbad Med")

# --- SECTION 1 : DOSSIER MÉDICAL ---
st.subheader("📋 Dossier Médical")
col_ant, col_traite = st.columns(2)

with col_ant:
    with st.expander("👨‍👩‍👧‍👦 Antécédents", expanded=True):
        with st.form("form_ant"):
            nouv_ant = st.text_area("Historique médical :", value=text_ant, height=100)
            if st.form_submit_button("Sauvegarder Antécédents"):
                conn.execute("UPDATE infos SET contenu=? WHERE type='ant'", (nouv_ant,))
                conn.commit()
                st.rerun()

with col_traite:
    with st.expander("💊 Traitement & Dosages", expanded=True):
        with st.form("form_traite"):
            nouv_traite = st.text_area("Médicaments actuels :", value=text_traite, height=100)
            if st.form_submit_button("Sauvegarder Traitement"):
                conn.execute("UPDATE infos SET contenu=? WHERE type='traite'", (nouv_traite,))
                conn.commit()
                st.rerun()

st.divider()

# --- SECTION 2 : SAISIE ---
c1, c2 = st.columns(2)
with c1:
    st.subheader("➕ Ajouter une Mesure")
    with st.form("add_form", clear_on_submit=True):
        date_c = st.text_input("Date", datetime.now().strftime("%d/%m/%Y"))
        heure_c = st.text_input("Heure", datetime.now().strftime("%H:%M"))
        sys_c = st.number_input("Systolique (Haut)", 40, 250, 120)
        dia_c = st.number_input("Diastolique (Bas)", 30, 150, 80)
        pouls_c = st.number_input("Pouls (BPM)", 0, 200, 70)
        gly_c = st.number_input("Glycémie (g/L)", 0.0, 5.0, 0.0)
        notes_c = st.text_input("Note / Observation")
        
        if st.form_submit_button("ENREGISTRER LA MESURE"):
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM mesures")
            max_id = cursor.fetchone()[0]
            new_id = (max_id + 1) if max_id else 10
            conn.execute("INSERT INTO mesures VALUES (?,?,?,?,?,?,?)", 
                         (new_id, sys_c, dia_c, pouls_c, gly_c, f"{date_c} {heure_c}", notes_c))
            conn.commit()
            st.success("Mesure bien enregistrée !")
            st.rerun()

with c2:
    st.subheader("📝 Modifier / Supprimer")
    if not df_mesures.empty:
        id_sel = st.selectbox("Sélectionner l'ID", df_mesures["id"].tolist())
        if st.button("🗑️ Supprimer cette ligne"):
            conn.execute("DELETE FROM mesures WHERE id=?", (id_sel,))
            conn.commit()
            st.rerun()
    else:
        st.write("Aucune donnée.")

st.divider()

# --- SECTION 3 : AFFICHAGE ---
st.subheader("📋 Historique des Mesures")
st.info("Référentiel : Normale < 130/80 mmHg | Hypertension > 140/90 mmHg")

st.dataframe(df_mesures, use_container_width=True, hide_index=True)

# Bouton de sauvegarde externe
csv = df_mesures.to_csv(index=False).encode('utf-8')
st.download_button("📥 Télécharger mon journal (CSV)", csv, "suivi_sante_houbad.csv", "text/csv")

st.markdown("<h3 style='text-align: center; color: grey;'>Élaboré par Houbad Douaa</h3>", unsafe_allow_html=True)
