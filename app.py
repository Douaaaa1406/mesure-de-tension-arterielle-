import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Santé - Houbad Med", layout="wide")

# Données de secours (récupérées de tes photos)
data_recuperee = [
    {"ID": 1, "SYS": 175, "DIA": 103, "Pouls": 56, "Glycemie": 0.0, "Date_Heure": "04/03/2026 17:45", "Notes": "Sans traitement; Vertige"},
    {"ID": 2, "SYS": 150, "DIA": 100, "Pouls": 0, "Glycemie": 1.33, "Date_Heure": "06/03/2026 14:10", "Notes": "vertige apres prière"},
    {"ID": 3, "SYS": 157, "DIA": 107, "Pouls": 52, "Glycemie": 0.0, "Date_Heure": "06/03/2026 16:30", "Notes": "Ancienne mesure"},
    {"ID": 4, "SYS": 150, "DIA": 100, "Pouls": 69, "Glycemie": 0.0, "Date_Heure": "06/03/2026 19:00", "Notes": "avant iftar"},
    {"ID": 5, "SYS": 154, "DIA": 98, "Pouls": 0, "Glycemie": 0.0, "Date_Heure": "06/03/2026 19:52", "Notes": "Ancienne mesure"},
    {"ID": 6, "SYS": 138, "DIA": 100, "Pouls": 68, "Glycemie": 0.0, "Date_Heure": "06/03/2026 20:30", "Notes": "Apres iftar (Zanidip)"},
    {"ID": 7, "SYS": 113, "DIA": 85, "Pouls": 70, "Glycemie": 2.29, "Date_Heure": "11/03/2026 21:00", "Notes": "Récupérée de photo"},
    {"ID": 8, "SYS": 133, "DIA": 90, "Pouls": 71, "Glycemie": 2.76, "Date_Heure": "06/03/2026 21:25", "Notes": "2H après Iftar"},
    {"ID": 9, "SYS": 135, "DIA": 86, "Pouls": 63, "Glycemie": 0.0, "Date_Heure": "07/03/2026 04:56", "Notes": "Shor"}
]

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_mesures = conn.read(worksheet="Mesures", ttl="0")
    if df_mesures.empty:
        df_mesures = pd.DataFrame(data_recuperee)
except Exception:
    df_mesures = pd.DataFrame(data_recuperee)

st.title("🩺 Journal de Bord : Houbad Med")

# --- ONGLETS POUR NAVIGUER ---
tab1, tab2 = st.tabs(["➕ Ajouter / Historique", "📝 Modifier une donnée"])

with tab1:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("➕ Nouvelle Mesure")
        with st.form("form_saisie", clear_on_submit=True):
            # Saisie manuelle de la date et l'heure
            date_texte = st.text_input("Date (ex: 12/03/2026)", datetime.now().strftime("%d/%m/%Y"))
            heure_texte = st.text_input("Heure (ex: 14:30)", datetime.now().strftime("%H:%M"))
            
            s_val = st.number_input("SYS", 40, 250, 120)
            di_val = st.number_input("DIA", 30, 150, 80)
            p_val = st.number_input("Pouls", 0, 200, 70)
            g_val = st.number_input("Glycémie", 0.0, 5.0, 0.0, step=0.01)
            o_val = st.text_input("Observations")
            
            if st.form_submit_button("ENREGISTRER"):
                new_row = pd.DataFrame([{
                    "ID": int(df_mesures["ID"].max() + 1 if not df_mesures.empty else 1),
                    "SYS": s_val, "DIA": di_val, "Pouls": p_val, "Glycemie": g_val,
                    "Date_Heure": f"{date_texte} {heure_texte}",
                    "Notes": o_val
                }])
                df_mesures = pd.concat([df_mesures, new_row], ignore_index=True)
                try:
                    conn.update(worksheet="Mesures", data=df_mesures)
                    st.success("Synchronisé avec succès !")
                except:
                    st.warning("Enregistré localement uniquement.")
                st.rerun()

    with col2:
        st.subheader("📋 Historique Permanent")
        if not df_mesures.empty:
            st.dataframe(df_mesures.iloc[::-1], use_container_width=True, hide_index=True)

with tab2:
    st.subheader("📝 Modifier ou Corriger une ligne")
    if not df_mesures.empty:
        id_a_modifier = st.selectbox("Sélectionnez l'ID de la mesure à modifier", df_mesures["ID"].tolist())
        
        # Récupérer les données actuelles de la ligne choisie
        ligne_actuelle = df_mesures[df_mesures["ID"] == id_a_modifier].iloc[0]
        
        with st.form("form_modif"):
            c1, c2 = st.columns(2)
            with c1:
                new_dt = st.text_input("Date & Heure", value=ligne_actuelle["Date_Heure"])
                new_sys = st.number_input("SYS", value=int(ligne_actuelle["SYS"]))
                new_dia = st.number_input("DIA", value=int(ligne_actuelle["DIA"]))
            with c2:
                new_p = st.number_input("Pouls", value=int(ligne_actuelle["Pouls"]))
                new_g = st.number_input("Glycémie", value=float(ligne_actuelle["Glycemie"]), step=0.01)
                new_o = st.text_input("Observations", value=ligne_actuelle["Notes"])
            
            if st.form_submit_button("METTRE À JOUR"):
                # Appliquer les modifications dans le DataFrame
                index_ligne = df_mesures[df_mesures["ID"] == id_a_modifier].index
                df_mesures.at[index_ligne[0], "Date_Heure"] = new_dt
                df_mesures.at[index_ligne[0], "SYS"] = new_sys
                df_mesures.at[index_ligne[0], "DIA"] = new_dia
                df_mesures.at[index_ligne[0], "Pouls"] = new_p
                df_mesures.at[index_ligne[0], "Glycemie"] = new_g
                df_mesures.at[index_ligne[0], "Notes"] = new_o
                
                try:
                    conn.update(worksheet="Mesures", data=df_mesures)
                    st.success("Modification enregistrée !")
                    st.rerun()
                except:
                    st.error("Erreur lors de la synchronisation.")
    else:
        st.info("Aucune donnée à modifier.")

st.divider()
st.markdown("<h3 style='text-align: center; color: grey;'>Élaboré par Houbad Douaa</h3>", unsafe_allow_html=True)
