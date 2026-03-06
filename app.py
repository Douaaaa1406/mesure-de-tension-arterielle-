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

# --- STYLE CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .patient-card { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        border-left: 10px solid #e63946; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        margin-bottom: 25px; 
    }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('sante_houbad_final.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  systolique INTEGER, diastolique INTEGER, 
                  battements INTEGER, glycemie REAL, date_heure TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS antecedents (id INTEGER PRIMARY KEY, texte TEXT)''')
    conn.commit()
    conn.close()

def ajouter_mesure(sys, dia, bpm, gly, dt):
    conn = sqlite3.connect('sante_houbad_final.db')
    c = conn.cursor()
    # CORRECTION : On utilise 'dt' (la date choisie) et non l'heure actuelle
    date_formatee = dt.strftime("%Y-%m-%d %H:%M") 
    c.execute("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure) VALUES (?, ?, ?, ?, ?)",
              (sys, dia, bpm, gly, date_formatee))
    conn.commit()
    conn.close()

def supprimer_mesure(id_mesure):
    conn = sqlite3.connect('sante_houbad_final.db')
    c = conn.cursor()
    c.execute("DELETE FROM mesures WHERE id = ?", (id_mesure,))
    conn.commit()
    conn.close()

def sauver_antecedents(texte):
    conn = sqlite3.connect('sante_houbad_final.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO antecedents (id, texte) VALUES (1, ?)", (texte,))
    conn.commit()
    conn.close()

def charger_donnees():
    conn = sqlite3.connect('sante_houbad_final.db')
    # On trie par date_heure pour que l'historique soit chronologique
    df = pd.read_sql_query("SELECT id, systolique, diastolique, battements, glycemie, date_heure FROM mesures ORDER BY date_heure DESC", conn)
    ant = conn.cursor().execute("SELECT texte FROM antecedents WHERE id=1").fetchone()
    conn.close()
    return df, ant[0] if ant else ""

init_db()
data, ant_text = charger_donnees()

# --- EN-TÊTE ---
st.markdown("""
    <div class="patient-card">
        <h1 style='margin:0;'>Patient : Houbad Med</h1>
        <p style='margin:0; color:#457b9d; font-weight:bold;'>Suivi Médical (Historique Chronologique)</p>
    </div>
    """, unsafe_allow_html=True)

col_gauche, col_droite = st.columns([1, 2], gap="large")

with col_gauche:
    st.subheader("👨‍👩‍👧‍👦 Antécédents Familiaux")
    new_ant = st.text_area("Notes :", value=ant_text, height=120)
    if st.button("💾 Sauvegarder"):
        sauver_antecedents(new_ant)
        st.success("Enregistré")

    st.divider()

    st.subheader("➕ Nouvelle Mesure")
    with st.form("form_saisie", clear_on_submit=True):
        st.write("**Date et Heure de la mesure**")
        c_dt1, c_dt2 = st.columns(2)
        with c_dt1:
            date_s = st.date_input("Jour", datetime.now())
        with c_dt2:
            heure_s = st.time_input("Heure", datetime.now().time())
        
        # On combine la date et l'heure choisies par l'utilisateur
        dt_final = datetime.combine(date_s, heure_s)

        c1, c2 = st.columns(2)
        with c1:
            sys = st.number_input("SYS", 40, 250, 120)
            bpm = st.number_input("Pouls", 30, 220, 70)
        with c2:
            dia = st.number_input("DIA", 30, 150, 80)
            gly = st.number_input("Glycémie", 0.0, 5.0, 1.0, step=0.01)
        
        if st.form_submit_button("✅ ENREGISTRER"):
            ajouter_mesure(sys, dia, bpm, gly, dt_final)
            st.rerun()

with col_droite:
    st.subheader("📋 Historique des mesures")
    
    if not data.empty:
        # Affichage du dernier relevé selon la DATE (pas l'ordre de saisie)
        dernier = data.iloc[0]
        m1, m2, m3 = st.columns(3)
        m1.metric("Tension", f"{int(dernier['systolique'])}/{int(dernier['diastolique'])}")
        m2.metric("Glycémie", f"{dernier['glycemie']} g/L")
        m3.metric("Date Mesure", dernier['date_heure'])

        st.markdown("---")
        
        st.dataframe(
            data.drop(columns=['id']), 
            use_container_width=True,
            column_config={
                "date_heure": st.column_config.TextColumn("📅 Date & Heure réelle"),
                "systolique": "SYS",
                "diastolique": "DIA",
                "battements": "Pouls",
                "glycemie": "Glycémie"
            }
        )

        with st.expander("🗑️ Supprimer une ligne"):
            id_del = st.selectbox("Ligne à effacer :", options=data['id'].tolist(),
                                  format_func=lambda x: data.loc[data['id']==x, 'date_heure'].values[0])
            if st.button("Supprimer définitivement"):
                supprimer_mesure(id_del)
                st.rerun()
    else:
        st.info("Aucune donnée.")
