import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Houbad Med", page_icon="🩺", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .patient-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #e63946; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 1px solid #dee2e6; }
    </style>
    """, unsafe_allow_header=True)

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('sante_houbad_v3.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mesures 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  systolique INTEGER, diastolique INTEGER, 
                  battements INTEGER, glycemie REAL, date_heure TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS antecedents (id INTEGER PRIMARY KEY, texte TEXT)''')
    conn.commit()
    conn.close()

def ajouter_mesure(sys, dia, bpm, gly, dt):
    conn = sqlite3.connect('sante_houbad_v3.db')
    c = conn.cursor()
    c.execute("INSERT INTO mesures (systolique, diastolique, battements, glycemie, date_heure) VALUES (?, ?, ?, ?, ?)",
              (sys, dia, bpm, gly, dt.strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    conn.close()

def supprimer_mesure(id_mesure):
    conn = sqlite3.connect('sante_houbad_v3.db')
    c = conn.cursor()
    c.execute("DELETE FROM mesures WHERE id = ?", (id_mesure,))
    conn.commit()
    conn.close()

def sauver_antecedents(texte):
    conn = sqlite3.connect('sante_houbad_v3.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO antecedents (id, texte) VALUES (1, ?)", (texte,))
    conn.commit()
    conn.close()

def charger_donnees():
    conn = sqlite3.connect('sante_houbad_v3.db')
    df = pd.read_sql_query("SELECT id, systolique, diastolique, battements, glycemie, date_heure FROM mesures ORDER BY id DESC", conn)
    ant = conn.cursor().execute("SELECT texte FROM antecedents WHERE id=1").fetchone()
    conn.close()
    return df, ant[0] if ant else ""

init_db()
data, ant_text = charger_donnees()

# --- INTERFACE ---
st.markdown(f'<div class="patient-card"><h1 style="margin:0;">Patient : Houbad Med</h1><p style="color:gray;">Suivi Multi-paramètres</p></div>', unsafe_allow_header=True)

col_left, col_right = st.columns([1, 2])

with col_left:
    # --- SECTION ANTÉCÉDENTS ---
    st.subheader("👨‍👩‍👧‍👦 Antécédents Familiaux")
    with st.container():
        new_ant = st.text_area("Historique médical familial :", value=ant_text, height=120, placeholder="Ex: Diabète type 2 (père), Hypertension (mère)...")
        if st.button("Sauvegarder les antécédents"):
            sauver_antecedents(new_ant)
            st.success("C'est enregistré !")

    st.divider()

    # --- FORMULAIRE DE SAISIE ---
    st.subheader("➕ Ajouter une Mesure")
    with st.form("form_saisie", clear_on_submit=True):
        st.write("Date et Heure (modifiable pour anciens relevés)")
        c_dt1, c_dt2 = st.columns(2)
        with c_dt1:
            date_s = st.date_input("Date", datetime.now())
        with c_dt2:
            heure_s = st.time_input("Heure", datetime.now().time())
        
        dt_final = datetime.combine(date_s, heure_s)

        c1, c2 = st.columns(2)
        with c1:
            sys = st.number_input("Tension SYS", 40, 250, 120)
            bpm = st.number_input("Pouls (BPM)", 30, 220, 70)
        with c2:
            dia = st.number_input("Tension DIA", 30, 150, 80)
            gly = st.number_input("Glycémie (g/L)", 0.0, 5.0, 1.0, step=0.01)
        
        if st.form_submit_button("ENREGISTRER LA DONNÉE"):
            ajouter_mesure(sys, dia, bpm, gly, dt_final)
            st.rerun()

with col_right:
    st.subheader("📋 Historique & Tableau de bord")
    
    if not data.empty:
        # Affichage du dernier état (Indicateurs)
        last = data.iloc[0]
        m1, m2, m3 = st.columns(3)
        m1.metric("Dernière Tension", f"{int(last['systolique'])}/{int(last['diastolique'])}")
        m2.metric("Dernier Pouls", f"{int(last['battements'])} BPM")
        m3.metric("Dernière Glycémie", f"{last['glycemie']} g/L")

        st.markdown("---")
        
        # Tableau récapitulatif (on cache l'ID pour l'utilisateur mais il est présent)
        st.dataframe(
            data.drop(columns=['id']), 
            use_container_width=True,
            column_config={
                "date_heure": "📅 Date & Heure",
                "systolique": "SYS",
                "diastolique": "DIA",
                "battements": "Pouls",
                "glycemie": "Glycémie (g/L)"
            }
        )

        # --- OPTION DE SUPPRESSION ---
        st.divider()
        with st.expander("🗑️ Supprimer une erreur de saisie"):
            id_a_supprimer = st.selectbox("Sélectionnez la date/heure de la ligne à supprimer", 
                                          options=data['id'].tolist(),
                                          format_func=lambda x: data.loc[data['id']==x, 'date_heure'].values[0])
            if st.button("Confirmer la suppression", type="primary"):
                supprimer_mesure(id_a_supprimer)
                st.warning("Ligne supprimée.")
                st.rerun()
    else:
        st.info("Aucune donnée enregistrée pour le moment.")

st.markdown("<br><center><small>Application privée - Suivi Houbad Med</small></center>", unsafe_allow_header=True)
