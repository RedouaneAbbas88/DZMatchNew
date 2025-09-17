import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="DZMatch Votes", layout="wide")
st.title("🏆 DZMatch Votes")

# -------------------------------
# 🔹 Définir les catégories et participants
# -------------------------------
categories = {
    "Meilleur gardien": [
        "Oussama Benbout (USMA)", "Zakaria Bouhalfaya (CSC)", "Abderrahmane Medjadel (ASO)",
        "Tarek Boussder (ESS)", "Abdelkader Salhi (MCEB)", "Zeghba (CRB)", "Hadid (JSK)", "Ramdane (MCA)"
    ],
    "Meilleur club": ["MCA", "USMA", "CSC", "CRB", "JSK", "PAC", "ESS"],
    "Meilleur joueur": [
        "Adel Boulbina (PAC)", "Aymen Mahious (CRB)", "Abderrahmane Meziane (CRB)",
        "Ibrahim Dib (CSC)", "Salim Boukhenchouch (USMA)", "Larbi Tabti (MCA)", "Mehdi Boudjamaa (JSK)"
    ],
    "Meilleur entraîneur": [
        "Khaled Benyahia (MCA)", "Joseph Zinbauer (JSK)", "Sead Ramovic (CRB)",
        "Khereddine Madoui (CSC)", "Bilal Dziri (PAC)"
    ]
}

# -------------------------------
# 🔹 Barème des points
# -------------------------------
points = {1:5, 2:4, 3:3, 4:2, 5:1}

# -------------------------------
# 🔹 Connexion à Google Sheets
# -------------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(creds)

# Nom du fichier Google Sheet
sheet = client.open("VoteDZMatch").sheet1

# -------------------------------
# 🔹 Nom du votant
# -------------------------------
nom_votant = st.text_input("📝 Entrez votre nom et prénom :")

# -------------------------------
# 🔹 Formulaire de vote
# -------------------------------
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

# -------------------------------
# 🔹 Sauvegarde du vote
# -------------------------------
def save_vote(nom, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Si le votant a déjà voté
    if not df.empty and nom in df["Nom"].values:
        return False

    # Ajouter les votes
    for cat, top5 in votes.items():
        for i, candidat in enumerate(top5, start=1):
            sheet.append_row([nom, cat, candidat, i, points.get(i,0)])
    return True

# -------------------------------
# 🔹 Traitement du vote
# -------------------------------
if submitted:
    if not nom_votant.strip():
        st.error("⚠️ Vous devez entrer votre nom et prénom avant de voter.")
    else:
        success = save_vote(nom_votant, vote_data)
        if success:
            st.success(f"Merci {nom_votant}, votre vote a été enregistré ! 🎉")
        else:
            st.error("⚠️ Vous avez déjà voté.")

# -------------------------------
# 🔹 Affichage des résultats
# -------------------------------
st.header("📊 Classements en temps réel")
data = sheet.get_all_records()
if data:
    df = pd.DataFrame(data)
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")

    for cat in categories:
        st.subheader(cat)
        df_cat = df[df["Categorie"]==cat].groupby("Candidat")["Points"].sum().reset_index()
        df_cat = df_cat.sort_values(by="Points", ascending=False)
        df_cat.insert(0,"Position", range(1, len(df_cat)+1))
        st.dataframe(df_cat, use_container_width=True)
else:
    st.info("Aucun vote pour le moment.")
