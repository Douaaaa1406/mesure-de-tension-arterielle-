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
    conn = sqlite3.connect('suivi_houbad_v18.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  systolique INTEGER, diastolique INTEGER, 
                  battements INTEGER, glycemie REAL, 
                  date_heure TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS antecedents (id INTEGER PRIMARY KEY, texte TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS traitements (id INTEGER PRIMARY KEY, texte TEXT)''')
    
    # Insertion des données historiques si vide
    c.execute("SELECT COUNT(*) FROM mesures")
    if c.fetchone()[0] == 0:
        anciennes_valeurs = [
            (150, 100, 0,  1.33, "06/03/2026 14:10", "vertige apres prière"),
            (157, 107, 52, 0.0,  "06/03/2026 16:30", "Ancienne mesure"),
            (150, 100, 69, 0.0,  "06/03/2026 19:00", "avant iftar"),
            (138, 100, 68, 0.0,  "06/03/2026 20:30", "Apres iftar (Zanidip)")
        ]
        c.executemany("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure, notes) VALUES (?, ?, ?, ?, ?, ?)", anciennes_valeurs)
    
    conn.commit()
    conn.close()

def charger_data():
    conn = sqlite3.connect('suivi_houbad_v18.db')
    df = pd.read_sql_query("SELECT * FROM mesures ORDER BY id ASC", conn)
    ant = conn.cursor().execute("SELECT texte FROM antecedents WHERE id=1").fetchone()
    traite = conn.cursor().execute("SELECT texte FROM traitements WHERE id=1").fetchone()
    conn.close()
    return df, ant[0] if ant else "", traite[0] if traite else ""

init_db()
df_mesures, text_ant, text_traite = charger_data()

# --- INTERFACE ---
st.title("🩺 Journal de Bord : Houbad Med")

# --- SECTION 1 : INFORMATIONS MÉDICALES FIXES ---
st.subheader("📋 Dossier Médical")
col_ant, col_traite = st.columns(2)

with col_ant:
    with st.expander("👨‍👩‍👧‍👦 Antécédents Médicaux", expanded=True):
        with st.form("form_ant"):
            nouveau_ant = st.text_area("Historique :", value=text_ant, height=100)
            if st.form_submit_button("Sauvegarder Antécédents"):
                conn = sqlite3.connect('suivi_houbad_v18.db')
                conn.cursor().execute("INSERT OR REPLACE INTO antecedents (id, texte) VALUES (1, ?)", (nouveau_ant,))
                conn.commit()
                conn.close()
                st.rerun()

with col_traite:
    with st.expander("💊 Traitement & Grammage", expanded=True):
        with st.form("form_traite"):
            nouveau_traite = st.text_area("Médicaments et dosages :", value=text_traite, height=100)
            if st.form_submit_button("Sauvegarder Traitement"):
                conn = sqlite3.connect('suivi_houbad_v18.db')
                conn.cursor().execute("INSERT OR REPLACE INTO traitements (id, texte) VALUES (1, ?)", (nouveau_traite,))
                conn.commit()
                conn.close()
                st.rerun()

st.divider()

# --- SECTION 2 : AJOUT ET MODIFICATION ---
col_ajout, col_modif = st.columns([1, 1], gap="large")

with col_ajout:
    st.subheader("➕ Ajouter une Mesure")
    with st.form("form_saisie", clear_on_submit=True):
        d_in = st.text_input("Date (JJ/MM/AAAA)", datetime.now().strftime("%d/%m/%Y"))
        t_in = st.text_input("Heure (HH:MM)", datetime.now().strftime("%H:%M"))
        c1, c2 = st.columns(2)
        with c1:
            s = st.number_input("SYS", 40, 250, 120)
            b = st.number_input("Pouls", 0, 200, 70)
        with c2:
            di = st.number_input("DIA", 30, 150, 80)
            g = st.number_input("Glycémie", 0.0, 5.0, 0.0, step=0.01)
        n = st.text_input("Observations")
        if st.form_submit_button("ENREGISTRER LA MESURE"):
            conn = sqlite3.connect('suivi_houbad_v18.db')
            dt_str = f"{d_in} {t_in}"
            conn.cursor().execute("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                  (s, di, b, g, dt_str, n))
            conn.commit()
            conn.close()
            st.rerun()

with col_modif:
    st.subheader("📝 Modifier une donnée")
    if not df_mesures.empty:
        id_sel = st.selectbox("Choisir l'ID à corriger", df_mesures["id"].tolist())
        ligne = df_mesures[df_mesures["id"] == id_sel].iloc[0]
        
        with st.form("form_edit"):
            new_dt = st.text_input("Date/Heure", value=ligne["date_heure"])
            cc1, cc2 = st.columns(2)
            with cc1:
                new_s = st.number_input("SYS", value=int(ligne["systolique"]))
                new_di = st.number_input("DIA", value=int(ligne["diastolique"]))
            with cc2:
                new_b = st.number_input("Pouls", value=int(ligne["battements"]))
                new_g = st.number_input("Glycémie", value=float(ligne["glycemie"]))
            new_n = st.text_input("Note", value=ligne["notes"])
            
            if st.form_submit_button("APPLIQUER LES MODIFICATIONS"):
                conn = sqlite3.connect('suivi_houbad_v18.db')
                conn.cursor().execute("""UPDATE mesures SET systolique=?, diastolique=?, battements=?, 
                                         glycemie=?, date_heure=?, notes=? WHERE id=?""",
                                      (new_s, new_di, new_b, new_g, new_dt, new_n, id_sel))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.write("Rien à modifier")

st.divider()

# --- SECTION 3 : HISTORIQUE ---
st.subheader("📋 Historique Complet")


[Image of blood pressure categories chart]

if not df_mesures.empty:
    st.dataframe(
        df_mesures.iloc[::-1].rename(columns={
            "id": "ID", "systolique": "SYS", "diastolique": "DIA", 
            "battements": "Pouls", "glycemie": "Glycémie", 
            "date_heure": "Date/Heure", "notes": "Observations"
        }), 
        use_container_width=True,
        hide_index=True
    )

    with st.expander("🗑️ Supprimer définitivement une ligne"):
        to_del = st.number_input("ID à supprimer", min_value=1, step=1)
        if st.button("Confirmer Suppression"):
            conn = sqlite3.connect('suivi_houbad_v18.db')
            conn.cursor().execute("DELETE FROM mesures WHERE id = ?", (to_del,))
            conn.commit()
            conn.close()
            st.rerun()

st.markdown("<h3 style='text-align: center; color: grey;'>Élaboré par Houbad Douaa</h3>", unsafe_allow_html=True)
