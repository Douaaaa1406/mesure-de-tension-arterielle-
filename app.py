import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Santé - Houbad Med", layout="wide")

# Connexion sécurisée à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Fonction pour charger les données
def load_data():
    try:
        df = conn.read(worksheet="Mesures", ttl="0")
        # Si le fichier est vide, on met tes données récupérées
        if df.empty:
            data = [
                {"ID": 1, "SYS": 175, "DIA": 103, "Pouls": 56, "Glycemie": 0.0, "Date_Heure": "04/03/2026 17:45", "Notes": "Sans traitement zanidip; Vertige"},
                {"ID": 2, "SYS": 150, "DIA": 100, "Pouls": 0, "Glycemie": 1.33, "Date_Heure": "06/03/2026 14:10", "Notes": "vertige apres prière"},
                {"ID": 3, "SYS": 157, "DIA": 107, "Pouls": 52, "Glycemie": 0.0, "Date_Heure": "06/03/2026 16:30", "Notes": "Ancienne mesure"},
                {"ID": 4, "SYS": 150, "DIA": 100, "Pouls": 69, "Glycemie": 0.0, "Date_Heure": "06/03/2026 19:00", "Notes": "avant iftar"},
                {"ID": 5, "SYS": 154, "DIA": 98, "Pouls": 0, "Glycemie": 0.0, "Date_Heure": "06/03/2026 19:52", "Notes": "Ancienne mesure"},
                {"ID": 6, "SYS": 138, "DIA": 100, "Pouls": 68, "Glycemie": 0.0, "Date_Heure": "06/03/2026 20:30", "Notes": "Apres iftar (Zanidip)"},
                {"ID": 7, "SYS": 113, "DIA": 85, "Pouls": 70, "Glycemie": 2.29, "Date_Heure": "11/03/2026 21:00", "Notes": "Récupérée de photo"},
                {"ID": 8, "SYS": 133, "DIA": 90, "Pouls": 71, "Glycemie": 2.76, "Date_Heure": "06/03/2026 21:25", "Notes": "2H après Iftar"},
                {"ID": 9, "SYS": 135, "DIA": 86, "Pouls": 63, "Glycemie": 0.0, "Date_Heure": "07/03/2026 04:56", "Notes": "Shor"}
            ]
            df = pd.DataFrame(data)
        return df
    except:
        return pd.DataFrame(columns=["ID", "SYS", "DIA", "Pouls", "Glycemie", "Date_Heure", "Notes"])

df_mesures = load_data()

st.title("🩺 Journal de Bord Houbad Med - Sauvegarde Permanente")

# --- INTERFACE DE SAISIE ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ Ajouter Mesure")
    with st.form("main_form", clear_on_submit=True):
        date_val = st.date_input("Date", datetime.now())
        heure_val = st.time_input("Heure", datetime.now().time())
        sys = st.number_input("SYS", 40, 250, 120)
        dia = st.number_input("DIA", 30, 150, 80)
        pouls = st.number_input("Pouls", 0, 200, 70)
        gly = st.number_input("Glycémie (g/L)", 0.0, 5.0, 0.0, step=0.01)
        note = st.text_input("Observations")
        
        if st.form_submit_button("SAUVEGARDER"):
            new_data = pd.DataFrame([{
                "ID": len(df_mesures) + 1,
                "SYS": sys,
                "DIA": dia,
                "Pouls": pouls,
                "Glycemie": gly,
                "Date_Heure": datetime.combine(date_val, heure_val).strftime("%d/%m/%Y %H:%M"),
                "Notes": note
            }])
            updated_df = pd.concat([df_mesures, new_data], ignore_index=True)
            conn.update(worksheet="Mesures", data=updated_df)
            st.success("Donnée envoyée au Google Sheets !")
            st.rerun()

with col2:
    st.subheader("📋 Historique (Sauvegardé sur Google Drive)")
    if not df_mesures.empty:
        # Tri pour voir les plus récents en haut
        st.dataframe(df_mesures.sort_values(by="Date_Heure", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("En attente de connexion au Google Sheets...")

st.divider()
st.markdown("<h3 style='text-align: center; color: grey;'>Élaboré par Houbad Douaa</h3>", unsafe_allow_html=True)
