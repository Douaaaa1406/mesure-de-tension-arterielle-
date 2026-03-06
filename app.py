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

# --- STYLE CSS (CORRIGÉ) ---
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
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    h1, h2, h3 { color: #1d3557; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('sante_houbad_final.db')
    c = conn.cursor()
    # Table des mesures
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  systolique INTEGER, diastolique INTEGER, 
                  battements INTEGER, glycemie REAL, date_heure TEXT)''')
    # Table des antécédents
    c.execute('''CREATE TABLE IF NOT EXISTS antecedents (id INTEGER PRIMARY KEY, texte TEXT)''')
    conn.commit()
    conn.close()

def ajouter_mesure(sys, dia, bpm, gly, dt):
    conn = sqlite3.connect('sante_houbad_final.db')
    c = conn.cursor()
    date_str = dt.strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure) VALUES (?, ?, ?, ?, ?)",
              (sys, dia, bpm, gly, date_str))
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
    df = pd.read_sql_query("SELECT id, systolique, diastolique, battements, glycemie, date_heure FROM mesures ORDER BY id DESC", conn)
    ant = conn.cursor().execute("SELECT texte FROM antecedents WHERE id=1").fetchone()
    conn.close()
    return df, ant[0] if ant else ""

# Initialisation
init_db()
data, ant_text = charger_donnees()

# --- EN-TÊTE ---
st.markdown("""
    <div class="patient-card">
        <h1 style='margin:0;'>Patient : Houbad Med</h1>
        <p style='margin:0; color:#457b9d; font-weight:bold;'>Système de Suivi Médical Partagé</p>
    </div>
    """, unsafe_allow_html=True)

# --- MISE EN PAGE PRINCIPALE ---
col_gauche, col_droite = st.columns([1, 2], gap="large")

with col_gauche:
    # SECTION ANTÉCÉDENTS
    st.subheader("👨‍👩‍👧‍👦 Antécédents Familiaux")
    new_ant = st.text_area("Notes importantes :", value=ant_text, height=150, placeholder="Inscrivez ici les maladies chroniques ou antécédents de la famille...")
    if st.button("💾 Sauvegarder les notes"):
        sauver_antecedents(new_ant)
        st.success("Notes mises à jour !")

    st.divider()

    # FORMULAIRE DE SAISIE
    st.subheader("➕ Nouvelle Mesure")
    with st.form("form_saisie", clear_on_submit=True):
        st.write("**Date et Heure (modifiable)**")
        c_dt1, c_dt2 = st.columns(2)
        with c_dt1:
            date_s = st.date_input("Jour", datetime.now())
        with c_dt2:
            heure_s = st.time_input("Heure", datetime.now().time())
        
        dt_final = datetime.combine(date_s, heure_s)

        st.write("**Valeurs relevées**")
        c1, c2 = st.columns(2)
        with c1:
            sys = st.number_input("SYS (Max)", 40, 250, 120)
            bpm = st.number_input("Pouls (BPM)", 30, 220, 70)
        with c2:
            dia = st.number_input("DIA (Min)", 30, 150, 80)
            gly = st.number_input("Glycémie (g/L)", 0.0, 5.0, 1.0, step=0.01)
        
        if st.form_submit_button("✅ ENREGISTRER LA DONNÉE"):
            ajouter_mesure(sys, dia, bpm, gly, dt_final)
            st.rerun()

with col_droite:
    st.subheader("📋 Historique Médical")
    
    if not data.empty:
        # Cartes de résumé
        dernier = data.iloc[0]
        m1, m2, m3 = st.columns(3)
        m1.metric("Tension", f"{int(dernier['systolique'])}/{int(dernier['diastolique'])}", delta_color="inverse")
        m2.metric("Glycémie", f"{dernier['glycemie']} g/L")
        m3.metric("Pouls", f"{int(dernier['battements'])} BPM")

        st.markdown("---")
        
        # Tableau des données
        st.dataframe(
            data.drop(columns=['id']), 
            use_container_width=True,
            column_config={
                "date_heure": "📅 Date & Heure",
                "systolique": "SYS (mmHg)",
                "diastolique": "DIA (mmHg)",
                "battements": "Pouls (BPM)",
                "glycemie": "Glycémie (g/L)"
            }
        )

        # GESTION DE LA SUPPRESSION
        st.write("")
        with st.expander("🗑️ Supprimer une ligne erronée"):
            id_del = st.selectbox(
                "Choisir la mesure à effacer :", 
                options=data['id'].tolist(),
                format_func=lambda x: data.loc[data['id']==x, 'date_heure'].values[0]
            )
            if st.button("Confirmer la suppression", type="primary"):
                supprimer_mesure(id_del)
                st.toast("Donnée supprimée !")
                st.rerun()
    else:
        st.info("Aucune donnée enregistrée pour Houbad Med. Utilisez le formulaire à gauche pour commencer.")

# PIED DE PAGE
st.markdown("<br><hr><center><p style='color:gray;'>Application de suivi privée - Houbad Med - 2026</p></center>", unsafe_allow_html=True)
