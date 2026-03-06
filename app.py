import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Houbad Med", layout="wide")

# --- LOGIQUE BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('sante_houbad_v4.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  systolique INTEGER, diastolique INTEGER, 
                  battements INTEGER, glycemie REAL, date_heure TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS antecedents (id INTEGER PRIMARY KEY, texte TEXT)''')
    conn.commit()
    conn.close()

def ajouter_mesure(sys, dia, bpm, gly, dt):
    conn = sqlite3.connect('sante_houbad_v4.db')
    c = conn.cursor()
    date_str = dt.strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure) VALUES (?, ?, ?, ?, ?)",
              (sys, dia, bpm, gly, date_str))
    conn.commit()
    conn.close()

def supprimer_mesure(id_m):
    conn = sqlite3.connect('sante_houbad_v4.db')
    c = conn.cursor()
    c.execute("DELETE FROM mesures WHERE id = ?", (id_m,))
    conn.commit()
    conn.close()

def sauver_ant(t):
    conn = sqlite3.connect('sante_houbad_v4.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO antecedents (id, texte) VALUES (1, ?)", (t,))
    conn.commit()
    conn.close()

def charger_data():
    conn = sqlite3.connect('sante_houbad_v4.db')
    df = pd.read_sql_query("SELECT * FROM mesures ORDER BY date_heure DESC", conn)
    ant = conn.cursor().execute("SELECT texte FROM antecedents WHERE id=1").fetchone()
    conn.close()
    return df, ant[0] if ant else ""

init_db()
df_mesures, text_ant = charger_data()

# --- INTERFACE SIMPLE (SANS HTML COMPLEXE) ---
st.title("🩺 Patient : Houbad Med")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📝 Saisie & Infos")
    
    # Antécédents
    exp = st.expander("👨‍👩‍👧‍👦 Antécédents Familiaux", expanded=True)
    with exp:
        new_txt = st.text_area("Notes :", value=text_ant, height=100)
        if st.button("Enregistrer Notes"):
            sauver_ant(new_txt)
            st.rerun()

    st.subheader("➕ Ajouter Mesure")
    with st.form("form_med"):
        d = st.date_input("Date", datetime.now())
        t = st.time_input("Heure", datetime.now().time())
        val_sys = st.number_input("Systolique (SYS)", 40, 250, 120)
        val_dia = st.number_input("Diastolique (DIA)", 30, 150, 80)
        val_bpm = st.number_input("Pouls (BPM)", 30, 200, 70)
        val_gly = st.number_input("Glycémie (g/L)", 0.0, 5.0, 1.0, step=0.01)
        
        if st.form_submit_button("VALIDER"):
            dt_comb = datetime.combine(d, t)
            ajouter_mesure(val_sys, val_dia, val_bpm, val_gly, dt_comb)
            st.rerun()

with col2:
    st.header("📊 Historique")
    
    if not df_mesures.empty:
        # Dernières valeurs
        last = df_mesures.iloc[0]
        c_a, c_b, c_c = st.columns(3)
        c_a.metric("Tension", f"{int(last['systolique'])}/{int(last['diastolique'])}")
        c_b.metric("Glycémie", f"{last['glycemie']} g/L")
        c_c.metric("Date", last['date_heure'])

        st.write("")
        st.dataframe(df_mesures.drop(columns=['id']), use_container_width=True)

        # Suppression
        with st.expander("🗑️ Supprimer une ligne"):
            to_del = st.selectbox("Sélectionner la mesure", options=df_mesures['id'].tolist(),
                                  format_func=lambda x: df_mesures.loc[df_mesures['id']==x, 'date_heure'].values[0])
            if st.button("Confirmer Suppression"):
                supprimer_mesure(to_del)
                st.rerun()
    else:
        st.write("Aucune donnée pour le moment.")
