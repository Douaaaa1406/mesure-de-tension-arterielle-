import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Suivi Santé - Houbad Med", page_icon="🩺", layout="wide")

# Connexion à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CHARGEMENT DES DONNÉES ---
def load_all_data():
    try:
        df_m = conn.read(worksheet="Mesures", ttl="0")
        df_i = conn.read(worksheet="Infos", ttl="0")
    except:
        # Structure par défaut si Sheets est vide
        df_m = pd.DataFrame(columns=["ID", "SYS", "DIA", "Pouls", "Glycemie", "Date_Heure", "Notes"])
        df_i = pd.DataFrame([
            {"Type": "Antecedents", "Contenu": ""}, 
            {"Type": "Traitements", "Contenu": ""}
        ])
    return df_m, df_i

df_mesures, df_infos = load_all_data()

# Sécurité si df_infos est mal chargé
if df_infos.empty or len(df_infos) < 2:
    df_infos = pd.DataFrame([
        {"Type": "Antecedents", "Contenu": ""}, 
        {"Type": "Traitements", "Contenu": ""}
    ])

ant_val = df_infos.loc[df_infos["Type"] == "Antecedents", "Contenu"].values[0]
traite_val = df_infos.loc[df_infos["Type"] == "Traitements", "Contenu"].values[0]

st.title("🩺 Journal de Bord : Houbad Med")

# --- SECTION 1 : DOSSIER MÉDICAL (Antécédents et Traitements) ---
st.subheader("📋 Dossier Médical")
col_ant, col_traite = st.columns(2)

with col_ant:
    with st.expander("👨‍👩‍👧‍👦 Antécédents Médicaux", expanded=True):
        with st.form("form_ant"):
            nouveau_ant = st.text_area("Historique :", value=ant_val, height=100)
            if st.form_submit_button("Sauvegarder Antécédents"):
                df_infos.loc[df_infos["Type"] == "Antecedents", "Contenu"] = nouveau_ant
                conn.update(worksheet="Infos", data=df_infos)
                st.success("Antécédents mis à jour !")
                st.rerun()

with col_traite:
    with st.expander("💊 Traitement & Grammage", expanded=True):
        with st.form("form_traite"):
            nouveau_traite = st.text_area("Médicaments et dosages :", value=traite_val, height=100)
            if st.form_submit_button("Sauvegarder Traitement"):
                df_infos.loc[df_infos["Type"] == "Traitements", "Contenu"] = nouveau_traite
                conn.update(worksheet="Infos", data=df_infos)
                st.success("Traitement mis à jour !")
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
            new_id = int(df_mesures["ID"].max() + 1) if not df_mesures.empty else 1
            new_row = pd.DataFrame([{
                "ID": new_id, "SYS": s, "DIA": di, "Pouls": b, 
                "Glycemie": g, "Date_Heure": f"{d_in} {t_in}", "Notes": n
            }])
            df_mesures = pd.concat([df_mesures, new_row], ignore_index=True)
            conn.update(worksheet="Mesures", data=df_mesures)
            st.success("Enregistré dans Google Sheets !")
            st.rerun()

with col_modif:
    st.subheader("📝 Modifier une donnée")
    if not df_mesures.empty:
        id_sel = st.selectbox("Choisir l'ID à corriger", df_mesures["ID"].tolist())
        ligne = df_mesures[df_mesures["ID"] == id_sel].iloc[0]
        
        with st.form("form_edit"):
            new_dt = st.text_input("Date/Heure", value=str(ligne["Date_Heure"]))
            cc1, cc2 = st.columns(2)
            with cc1:
                edit_s = st.number_input("SYS", value=int(ligne["SYS"]))
                edit_di = st.number_input("DIA", value=int(ligne["DIA"]))
            with cc2:
                edit_b = st.number_input("Pouls", value=int(ligne["Pouls"]))
                edit_g = st.number_input("Glycémie", value=float(ligne["Glycemie"]))
            edit_n = st.text_input("Note", value=str(ligne["Notes"]))
            
            if st.form_submit_button("APPLIQUER LES MODIFICATIONS"):
                idx = df_mesures[df_mesures["ID"] == id_sel].index[0]
                df_mesures.at[idx, ["SYS", "DIA", "Pouls", "Glycemie", "Date_Heure", "Notes"]] = [
                    edit_s, edit_di, edit_b, edit_g, new_dt, edit_n
                ]
                conn.update(worksheet="Mesures", data=df_mesures)
                st.success("Modification réussie !")
                st.rerun()
    else:
        st.write("Aucune donnée à modifier.")

st.divider()

# --- SECTION 3 : HISTORIQUE ---
st.subheader("📋 Historique Complet (Google Sheets)")

# Rappel visuel des catégories de tension
# if not df_mesures.empty:
    st.dataframe(df_mesures.iloc[::-1], use_container_width=True, hide_index=True)

    with st.expander("🗑️ Supprimer une ligne"):
        to_del = st.number_input("ID à supprimer", min_value=1, step=1)
        if st.button("Confirmer Suppression"):
            df_mesures = df_mesures[df_mesures["ID"] != to_del]
            conn.update(worksheet="Mesures", data=df_mesures)
            st.success("Ligne supprimée !")
            st.rerun()

st.markdown("<h3 style='text-align: center; color: grey;'>Élaboré par Houbad Douaa</h3>", unsafe_allow_html=True)
