import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------
# ⚙️ Configuration Streamlit avec logo
# ---------------------------------------------------
st.set_page_config(
    page_title="DZBEST 2025",
    page_icon="Assets/logo.PNG",  # Remplacer par l'URL de ton logo
    layout="wide"
)

# Affichage du logo et du titre côte à côte
col1, col2 = st.columns([1, 5])
with col1:
    st.image("Assets/logo.PNG", width=150)  # Remplacer par l'URL de ton logo
with col2:
    st.title("DZBEST 2025")

# ---------------------------------------------------
# 🔹 Définir les catégories et participants
# ---------------------------------------------------
categories = {
    "Meilleur gardien": [
        "Oussama Benbout (USMA)", "Zakaria Bouhalfaya (CSC)",
        "Abderrahmane Medjadel (ASO)", "Tarek Boussder (ESS)",
        "Abdelkader Salhi (MCEB)", "Moustapha Zeghba (CRB)",
        "Hadid mohamed (JSK)", "Ramdane Abdelatif (MCA)"
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
# 🔹 Nombre max de choix par catégorie
# ---------------------------------------------------
max_choices = {
    "Meilleur gardien": 8,
    "Meilleur club": 7,
    "Meilleur joueur": 7,
    "Meilleur entraîneur": 5
}

# ---------------------------------------------------
# 🔹 Barème des points (jusqu’à TOP 8)
# ---------------------------------------------------
points = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}

# ---------------------------------------------------
# 🔹 Connexion Google Sheets
# ---------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds_dict = st.secrets["google"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)
SPREADSHEET_ID = "10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc"
spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet("Feuille 1")

# ---------------------------------------------------
# 🔹 Infos du votant (obligatoires)
# ---------------------------------------------------
nom_votant = st.text_input("📝 Entrez votre nom et prénom :")
num_tel = st.text_input("📞 Entrez votre numéro de téléphone :")
media_link = st.text_input("📸 Entrez le nom de votre média :")

# ---------------------------------------------------
# 🔹 Formulaire de vote
# ---------------------------------------------------
vote_data = {}
with st.form("vote_form"):
    for cat, participants in categories.items():
        st.subheader(cat)
        max_top = max_choices.get(cat, 5)
        top_selected = st.multiselect(
            f"Sélectionnez votre TOP {max_top} pour {cat} (ordre important)",
            options=participants,
            max_selections=max_top,
            key=cat
        )
        vote_data[cat] = top_selected

    submitted = st.form_submit_button("✅ Envoyer mon vote")

# ---------------------------------------------------
# 🔹 Fonction pour sauvegarder le vote
# ---------------------------------------------------
def save_vote(nom, tel, media, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Vérifier si le votant a déjà voté ou numéro de téléphone déjà utilisé
    if not df.empty:
        if "Nom" in df.columns and nom in df["Nom"].values:
            return False
        if "Téléphone" in df.columns and tel in df["Téléphone"].values:
            return False

    # Ajouter les votes
    new_rows = []
    for cat, top_selected in votes.items():
        for i, candidat in enumerate(top_selected, start=1):
            new_rows.append([nom, tel, media, cat, candidat, i, points.get(i, 0)])

    for row in new_rows:
        sheet.append_row(row)

    return True

# ---------------------------------------------------
# 🔹 Traitement du vote
# ---------------------------------------------------
if submitted:
    if not nom_votant.strip():
        st.error("⚠️ Vous devez entrer votre nom et prénom.")
    elif not num_tel.strip():
        st.error("⚠️ Vous devez entrer votre numéro de téléphone.")
    elif not media_link.strip():
        st.error("⚠️ Vous devez entrer le nom de votre média.")
    else:
        success = save_vote(nom_votant, num_tel, media_link, vote_data)
        if success:
            st.success(f"Merci {nom_votant}, votre vote a été enregistré ! 🎉")
        else:
            st.error("⚠️ Vous avez déjà voté ou ce numéro de téléphone a déjà été utilisé.")

# ---------------------------------------------------
# 🔹 Affichage des résultats
# ---------------------------------------------------
st.header("📊 Classements en temps réel")
data = sheet.get_all_records()
if data:
    df = pd.DataFrame(data)
    if "Points" in df.columns:
        df["Points"] = pd.to_numeric(df["Points"], errors="coerce")
        for cat in categories:
            st.subheader(cat)

            df_cat = (
                df[df["Categorie"] == cat]
                .groupby("Candidat")["Points"]
                .sum()
                .reset_index()
            )

            # Trier et réinitialiser proprement l'index
            df_cat = df_cat.sort_values(by="Points", ascending=False).reset_index(drop=True)

            # Ajouter la colonne Classement
            df_cat.insert(0, "Classement", range(1, len(df_cat) + 1))

            # Ne garder que les colonnes voulues
            df_cat = df_cat[["Classement", "Candidat", "Points"]]

            st.dataframe(df_cat, use_container_width=True)
