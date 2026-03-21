import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Suivi Santé - Houbad Med", page_icon="🩺", layout="wide")

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('sante_houbad_final.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY, 
                  sys INTEGER, dia INTEGER, pouls INTEGER, 
                  glycemie REAL, date_heure TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS infos (type TEXT PRIMARY KEY, contenu TEXT)''')
    
    # --- VOS MESURES HISTORIQUES (Mises à jour au 16/03/2026) ---
    mesures_historiques = [
        (1, 175, 103, 56, 0.0, "04/03/2026 17:45", "Sans traitement; Vertige"),
        (2, 150, 100, 0,  1.33, "06/03/2026 14:10", "vertige apres prière"),
        (3, 157, 107, 52, 0.0,  "06/03/2026 16:30", "Ancienne mesure"),
        (4, 150, 100, 69, 0.0,  "06/03/2026 19:00", "avant iftar"),
        (5, 154, 98,  0,  0.0,  "06/03/2026 19:52", "Ancienne mesure"),
        (6, 138, 100, 68, 0.0,  "06/03/2026 20:30", "Apres iftar (Zanidip)"),
        (7, 133, 90,  71, 2.76, "06/03/2026 21:25", "2H après Iftar"),
        (8, 135, 86,  63, 0.0,  "07/03/2026 04:56", "Shor"),
        (9, 113, 85,  70, 2.29, "11/03/2026 21:00", "zanidip a la priere"),
        (10, 123, 93, 0, 0.0, "15/03/2026 12:00", "Sayem"),
        (11, 130, 90, 0, 0.0, "16/03/2026 20:38", "apres ftor "),
        (12, 130, 90, 0, 0.0, "18/03/2026 19:10", "avant iftar"), 
        (13, 140, 92, 0, 1.80, "21/03/2026 20:18", "")
    ]
    
    for m in mesures_historiques:
        c.execute("INSERT OR IGNORE INTO mesures VALUES (?,?,?,?,?,?,?)", m)
    
    c.execute("INSERT OR IGNORE INTO infos VALUES ('ant', '')")
    c.execute("INSERT OR IGNORE INTO infos VALUES ('traite', '')")
    conn.commit()
    return conn

conn = init_db()

def charger_donnees():
    df = pd.read_sql_query("SELECT * FROM mesures ORDER BY id DESC", conn)
    ant_res = conn.execute("SELECT contenu FROM infos WHERE type='ant'").fetchone()
    traite_res = conn.execute("SELECT contenu FROM infos WHERE type='traite'").fetchone()
    ant = ant_res[0] if ant_res else ""
    traite = traite_res[0] if traite_res else ""
    return df, ant, traite

df_mesures, text_ant, text_traite = charger_donnees()

st.title("🩺 Journal de Bord : Houbad Med")

# --- SECTION 1 : DOSSIER MÉDICAL ---
st.subheader("📋 Dossier Médical")
col_a, col_t = st.columns(2)

with col_a:
    with st.expander("👨‍👩‍👧‍👦 Antécédents Médicaux", expanded=True):
        with st.form("form_ant"):
            nouv_ant = st.text_area("Historique :", value=text_ant, height=100)
            if st.form_submit_button("Sauvegarder Antécédents"):
                conn.execute("UPDATE infos SET contenu=? WHERE type='ant'", (nouv_ant,))
                conn.commit()
                st.success("Enregistré")
                st.rerun()

with col_t:
    with st.expander("💊 Traitement & Grammage", expanded=True):
        with st.form("form_traite"):
            nouv_traite = st.text_area("Dosages :", value=text_traite, height=100)
            if st.form_submit_button("Sauvegarder Traitement"):
                conn.execute("UPDATE infos SET contenu=? WHERE type='traite'", (nouv_traite,))
                conn.commit()
                st.success("Mis à jour")
                st.rerun()

st.divider()

# --- SECTION 2 : SAISIE ET MODIFICATION ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("➕ Ajouter une Mesure")
    with st.form("add_form", clear_on_submit=True):
        d_c = st.text_input("Date", datetime.now().strftime("%d/%m/%Y"))
        h_c = st.text_input("Heure", datetime.now().strftime("%H:%M"))
        s_c = st.number_input("SYS (Haut)", 40, 250, 120)
        di_c = st.number_input("DIA (Bas)", 30, 150, 80)
        p_c = st.number_input("Pouls", 0, 200, 70)
        g_c = st.number_input("Glycémie", 0.0, 5.0, 0.0)
        n_c = st.text_input("Observations")
        
        if st.form_submit_button("ENREGISTRER"):
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM mesures")
            max_id = cursor.fetchone()[0]
            new_id = (max_id + 1) if max_id else 12
            conn.execute("INSERT INTO mesures VALUES (?,?,?,?,?,?,?)", 
                         (new_id, s_c, di_c, p_c, g_c, f"{d_c} {h_c}", n_c))
            conn.commit()
            st.rerun()

with c2:
    st.subheader("📝 Modifier / Supprimer")
    if not df_mesures.empty:
        id_edit = st.selectbox("Choisir l'ID", df_mesures["id"].tolist())
        ligne_edit = df_mesures[df_mesures["id"] == id_edit].iloc[0]
        
        with st.form("edit_form"):
            e_s = st.number_input("Systolique", value=int(ligne_edit["sys"]))
            e_d = st.number_input("Diastolique", value=int(ligne_edit["dia"]))
            e_p = st.number_input("Pouls", value=int(ligne_edit["pouls"]))
            e_g = st.number_input("Glycémie", value=float(ligne_edit["glycemie"]))
            e_n = st.text_input("Note", value=str(ligne_edit["notes"]))
            
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.form_submit_button("✅ APPLIQUER"):
                conn.execute("UPDATE mesures SET sys=?, dia=?, pouls=?, glycemie=?, notes=? WHERE id=?", 
                             (e_s, e_d, e_p, e_g, e_n, id_edit))
                conn.commit()
                st.rerun()
                
            if btn_col2.form_submit_button("🗑️ SUPPRIMER"):
                conn.execute("DELETE FROM mesures WHERE id=?", (id_edit,))
                conn.commit()
                st.rerun()
    else:
        st.write("Pas de données.")

st.divider()

# --- SECTION 3 : HISTORIQUE ---
st.subheader("📋 Historique des Mesures")
st.info("Référentiel : Tension Normale < 130/80 | Hypertension > 140/90")

st.dataframe(df_mesures, use_container_width=True, hide_index=True)

csv_data = df_mesures.to_csv(index=False).encode('utf-8')
st.download_button("📥 Télécharger Sauvegarde (CSV)", csv_data, "journal_sante.csv", "text/csv")

st.markdown("<h3 style='text-align: center; color: grey;'>Élaboré par Houbad Douaa</h3>", unsafe_allow_html=True)
