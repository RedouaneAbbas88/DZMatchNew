import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------
# ⚙️ Configuration Streamlit
# ---------------------------------------------------
st.set_page_config(page_title="DZMatch Votes", layout="wide")
st.title("🏆 DZMatch Votes")

# ---------------------------------------------------
# 🔹 Définir les catégories et participants
# ---------------------------------------------------
categories = {
    "Meilleur gardien": [
        "abbas Benbout (USMA)", "Zakaria Bouhalfaya (CSC)",
        "Abderrahmane Medjadel (ASO)", "Tarek Boussder (ESS)",
        "Abdelkader Salhi (MCEB)", "Zeghba (CRB)",
        "Hadid (JSK)", "Ramdane (MCA)"
    ],
    "Meilleur club": ["MCA", "USMA", "CSC", "CRB", "JSK", "PAC", "ESS"],
    "Meilleur joueur": [
        "Adel Boulbina (PAC)", "Aymen Mahious (CRB)",
        "Abderrahmane Meziane (CRB)", "Ibrahim Dib (CSC)",
        "Salim Boukhenchouch (USMA)", "Larbi Tabti (MCA)",
        "Mehdi Boudjamaa (JSK)"
    ],
    "Meilleur entraîneur": [
        "Khaled Benyahia (MCA)", "Joseph Zinbauer (JSK)",
        "Sead Ramovic (CRB)", "Khereddine Madoui (CSC)", "Bilal Dziri (PAC)"
    ]
}

# ---------------------------------------------------
# 🔹 Barème des points
# ---------------------------------------------------
points = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# ---------------------------------------------------
# 🔹 Connexion Google Sheets
# ---------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google"]  # ton JSON dans .streamlit/secrets.toml
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

# Nom exact du fichier et de l’onglet
spreadsheet = client.open("votes")
sheet = spreadsheet.worksheet("FEUILLE 1")

# ---------------------------------------------------
# 🔹 Nom du votant
# ---------------------------------------------------
nom_votant = st.text_input("📝 Entrez votre nom et prénom :")

# ---------------------------------------------------
# 🔹 Formulaire de vote
# ---------------------------------------------------
vote_data = {}
with st.form("vote_form"):
    for cat, participants in categories.items():
        st.subheader(cat)
        top5 = st.multiselect(
            f"Sélectionnez votre TOP 5 pour {cat} (ordre important)",
            options=participants,
            max_selections=5,
            key=cat
        )
        vote_data[cat] = top5

    submitted = st.form_submit_button("✅ Envoyer mon vote")

# ---------------------------------------------------
# 🔹 Fonction pour sauvegarder le vote
# ---------------------------------------------------
def save_vote(nom, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Vérifier si le votant a déjà voté
    if not df.empty and nom in df["Nom"].values:
        return False

    # Ajouter les votes
    new_rows = []
    for cat, top5 in votes.items():
        for i, candidat in enumerate(top5, start=1):
            new_rows.append([nom, cat, candidat, i, points.get(i, 0)])

    # Envoi vers Google Sheets
    for row in new_rows:
        sheet.append_row(row)

    return True

# ---------------------------------------------------
# 🔹 Traitement du vote
# ---------------------------------------------------
if submitted:
    if not nom_votant.strip():
        st.error("⚠️ Vous devez entrer votre nom et prénom avant de voter.")
    else:
        success = save_vote(nom_votant, vote_data)
        if success:
            st.success(f"Merci {nom_votant}, votre vote a été enregistré ! 🎉")
        else:
            st.error("⚠️ Vous avez déjà voté.")

# ---------------------------------------------------
# 🔹 Affichage des résultats
# ---------------------------------------------------
st.header("📊 Classements en temps réel")

data = sheet.get_all_records()
if data:
    df = pd.DataFrame(data)
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")

    for cat in categories:
        st.subheader(cat)
        df_cat = df[df["Categorie"] == cat].groupby("Candidat")["Points"].sum().reset_index()
        df_cat = df_cat.sort_values(by="Points", ascending=False)
        df_cat.insert(0, "Position", range(1, len(df_cat) + 1))
        st.dataframe(df_cat, use_container_width=True)
