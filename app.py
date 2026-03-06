import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA BASE DE DONNÉES ---
def init_db():
    # Crée ou connecte la base de données locale
    conn = sqlite3.connect('sante_patient.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  systolique INTEGER, 
                  diastolique INTEGER, 
                  battements INTEGER, 
                  date_heure TEXT)''')
    conn.commit()
    conn.close()

def ajouter_mesure(sys, dia, bpm):
    conn = sqlite3.connect('sante_patient.db')
    c = conn.cursor()
    # Récupération de la date et l'heure actuelle
    maintenant = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO mesures (systolique, diastolique, battements, date_heure) VALUES (?, ?, ?, ?)",
              (sys, dia, bpm, maintenant))
    conn.commit()
    conn.close()

def charger_donnees():
    conn = sqlite3.connect('sante_patient.db')
    # On récupère les données triées de la plus récente à la plus ancienne
    df = pd.read_sql_query("SELECT systolique, diastolique, battements, date_heure FROM mesures ORDER BY id DESC", conn)
    conn.close()
    return df

# --- INTERFACE UTILISATEUR STREAMLIT ---
st.set_page_config(page_title="Suivi Tension Patient", layout="centered")
init_db()

st.title("🩺 Suivi de Tension")
st.info("Toutes les personnes ayant ce lien peuvent ajouter des mesures pour le patient.")

# Formulaire de saisie pour l'utilisateur
with st.form("form_saisie", clear_on_submit=True):
    st.subheader("Nouvelle mesure")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sys = st.number_input("SYS (Max)", min_value=40, max_value=250, value=120, help="Tension Systolique")
    with col2:
        dia = st.number_input("DIA (Min)", min_value=30, max_value=150, value=80, help="Tension Diastolique")
    with col3:
        bpm = st.number_input("BPM (Pouls)", min_value=30, max_value=220, value=70, help="Battements par minute")
    
    submit = st.form_submit_button("Enregistrer et rafraîchir")

# Logique après clic sur le bouton
if submit:
    ajouter_mesure(sys, dia, bpm)
    st.success("✅ Mesure enregistrée avec succès !")
    st.rerun() # Force le rafraîchissement immédiat du tableau

# Affichage des résultats sous forme de tableau
st.divider()
st.subheader("📋 Historique des mesures")

data = charger_donnees()

if not data.empty:
    # Renommer les colonnes pour un affichage plus propre
    data.columns = ["Systolique", "Diastolique", "Battements", "Date et Heure"]
    st.dataframe(data, use_container_width=True) # Tableau interactif
else:
    st.warning("Aucune donnée disponible. Soyez le premier à entrer une mesure !")
