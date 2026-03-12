import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Suivi Santé - Houbad Med", page_icon="🩺", layout="wide")

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('sante_houbad_v2.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY, 
                  sys INTEGER, dia INTEGER, pouls INTEGER, 
                  glycemie REAL, date_heure TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS infos (type TEXT PRIMARY KEY, contenu TEXT)''')
    
    # Données fournies par vos photos (ajustées)
    mesures_photos = [
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
    
    # Insertion des données de base si elles n'existent pas
    for m in mesures_photos:
        c.execute("INSERT OR IGNORE INTO mesures VALUES (?,?,?,?,?,?,?)", m)
    
    c.execute("INSERT OR IGNORE INTO infos VALUES ('ant', '')")
    c.execute("INSERT OR IGNORE INTO infos VALUES ('traite', '')")
    conn.commit()
    return conn

conn = init_db()

# --- RÉCUPÉRATION DES DONNÉES ---
df_mesures = pd.read_sql_query("SELECT * FROM mesures ORDER BY id DESC", conn)
ant_res = conn.execute("SELECT contenu FROM infos WHERE type='ant'").fetchone()
traite_res = conn.execute("SELECT contenu FROM infos WHERE type='traite'").fetchone()
text_ant = ant_res[0] if ant_res else ""
text_traite = traite_res[0] if traite_res else ""

st.title("🩺 Journal de Bord : Houbad Med")

# --- SECTION 1 : DOSSIER MÉDICAL ---
st.subheader("📋 Dossier Médical")
col_a, col_t = st.columns(2)

with col_a:
    with st.expander("👨‍👩‍👧‍👦 Antécédents", expanded=True):
        with st.form("f_ant"):
            n_ant = st.text_area("Historique :", value=text_ant, height=100)
            if st.form_submit_button("Enregistrer Antécédents"):
                conn.execute("UPDATE infos SET contenu=? WHERE type='ant'", (n_ant,))
                conn.commit()
                st.rerun()

with col_t:
    with st.expander("💊 Traitement Actuel", expanded=True):
        with st.form("f_traite"):
            n_traite = st.text_area("Médicaments et dosages :", value=text_traite, height=100)
            if st.form_submit_button("Enregistrer Traitement"):
                conn.execute("UPDATE infos SET contenu=? WHERE type='traite'", (n_traite,))
                conn.commit()
                st.rerun()

st.divider()

# --- SECTION 2 : AJOUT ET MODIFICATION ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("➕ Nouvelle Mesure")
    with st.form("add_form", clear_on_submit=True):
        d = st.text_input("Date", datetime.now().strftime("%d/%m/%Y"))
        t = st.text_input("Heure", datetime.now().strftime("%H:%M"))
        s = st.number_input("SYS (Tension Haute)", 40, 250, 120)
        di = st.number_input("DIA (Tension Basse)", 30, 150, 80)
        p = st.number_input("Pouls (BPM)", 0, 200, 70)
        g = st.number_input("Glycémie (g/L)", 0.0, 5.0, 0.0)
        obs = st.text_input("Observations / Notes")
        if st.form_submit_button("VALIDER L'ENREGISTREMENT"):
            # Calcul du nouvel ID
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM mesures")
            max_id = cursor.fetchone()[0]
            new_id = (max_id + 1) if max_id else 10
            
            conn.execute("INSERT INTO mesures (id, sys, dia, pouls, glycemie, date_heure, notes) VALUES (?,?,?,?,?,?,?)",
                         (new_id, s, di, p, g, f"{d} {t}", obs))
            conn.commit()
            st.success("Donnée enregistrée avec succès !")
            st.rerun()

with col2:
    st.subheader("📝 Modifier / Corriger")
    if not df_mesures.empty:
        id_sel = st.selectbox("Choisir l'ID de la ligne", df_mesures["id"].tolist())
        row = df_mesures[df_mesures["id"] == id_sel].iloc[0]
        with st.form("edit_form"):
            e_s = st.number_input("Corriger SYS", value=int(row["sys"]))
            e_d = st.number_input("Corriger DIA", value=int(row["dia"]))
            e_n = st.text_input("Modifier Note", value=str(row["notes"]))
            if st.form_submit_button("APPLIQUER LA CORRECTION"):
                conn.execute("UPDATE mesures SET sys=?, dia=?, notes=? WHERE id=?", (e_s, e_d, e_n, id_sel))
                conn.commit()
                st.rerun()

st.divider()

# --- SECTION 3 : HISTORIQUE ---
st.subheader("📋 Historique des Mesures")


[Image of blood pressure categories chart]

st.dataframe(df_mesures, use_container_width=True, hide_index=True)

# Bouton de secours pour sauvegarder vos données ailleurs
csv = df_mesures.to_csv(index=False).encode('utf-8')
st.download_button("📥 Télécharger une copie de sauvegarde (CSV)", csv, "suivi_sante.csv", "text/csv")

st.markdown("<h3 style='text-align: center; color: grey;'>Élaboré par Houbad Douaa</h3>", unsafe_allow_html=True)
