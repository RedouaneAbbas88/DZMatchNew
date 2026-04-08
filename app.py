import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="DZBEST 2025", layout="wide")
st.title("🏆 DZBEST 2025")

# ---------------------------------------------------
# DONNÉES AVEC PHOTOS
# ---------------------------------------------------
categories = {
    "Meilleur joueur": [
        {"name": "Adel Boulbina (PAC)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Adel_Boulbina.jpg"},
        {"name": "Aymen Mahious (CRB)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Abderrahmane Meziane (CRB)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Ibrahim Dib (CSC)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Salim Boukhenchouch (USMA)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Larbi Tabti (MCA)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Mehdi Boudjamaa (JSK)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"}
    ],
    "Meilleur gardien": [
        {"name": "Oussama Benbout (USMA)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Zakaria Bouhalfaya (CSC)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Abderrahmane Medjadel (ASO)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Tarek Boussder (ESS)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Abdelkader Salhi (MCEB)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Moustapha Zeghba (CRB)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"}
    ],
    "Meilleur entraîneur": [
        {"name": "Khaled Benyahia (MCA)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Joseph Zinbauer (JSK)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Sead Ramovic (CRB)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Khereddine Madoui (CSC)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"},
        {"name": "Bilal Dziri (PAC)", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Club_Placeholder.png"},
        {"name": "USMA", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Club_Placeholder.png"},
        {"name": "CSC", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Club_Placeholder.png"},
        {"name": "CRB", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Club_Placeholder.png"},
        {"name": "JSK", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Club_Placeholder.png"},
        {"name": "PAC", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Club_Placeholder.png"},
        {"name": "ESS", "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Club_Placeholder.png"}
    ]
}

max_choices = {cat: 5 for cat in categories}
points = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# ---------------------------------------------------
# GOOGLE SHEETS
# ---------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google"], scopes=SCOPES
)
client = gspread.authorize(creds)
sheet = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")

# ---------------------------------------------------
# INFOS VOTANT
# ---------------------------------------------------
nom = st.text_input("📝 Nom et prénom")
tel = st.text_input("📞 Téléphone")
media = st.text_input("📸 Média")

# ---------------------------------------------------
# VOTE DYNAMIQUE AVEC PHOTOS
# ---------------------------------------------------
vote_data = {}

for cat, participants in categories.items():
    st.subheader(f"🏅 {cat}")

    selections = []

    for i in range(1, max_choices[cat] + 1):

        available_options = [p["name"] for p in participants if p["name"] not in selections]

        choice = st.selectbox(
            f"{cat} - Choix #{i}",
            ["-- Choisir --"] + available_options,
            key=f"{cat}_{i}"
        )

        if choice != "-- Choisir --":
            selections.append(choice)

            # afficher image
            for p in participants:
                if p["name"] == choice:
                    st.image(p["img"], width=60)

    vote_data[cat] = selections

# ---------------------------------------------------
# SAVE
# ---------------------------------------------------
def save_vote(nom, tel, media, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        if "Nom" in df.columns and nom in df["Nom"].values:
            return False
        if "Téléphone" in df.columns and tel in df["Téléphone"].values:
            return False

    rows = []
    for cat, selections in votes.items():
        for i, candidat in enumerate(selections, start=1):
            rows.append([nom, tel, media, cat, candidat, i, points.get(i, 0)])

    for r in rows:
        sheet.append_row(r)

    return True

# BOUTON ENVOI
if st.button("✅ Envoyer mon vote"):

    if not nom.strip():
        st.error("⚠️ Entrez votre nom")
    elif not tel.strip():
        st.error("⚠️ Entrez votre téléphone")
    elif not media.strip():
        st.error("⚠️ Entrez votre média")
    else:
        ok = save_vote(nom, tel, media, vote_data)
        if ok:
            st.success("✅ Vote enregistré !")
        else:
            st.error("⚠️ Vous avez déjà voté")

# ---------------------------------------------------
# RESULTATS
# ---------------------------------------------------
st.header("📊 Classements")

data = sheet.get_all_records()

if data:
    df = pd.DataFrame(data)
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")

    for cat in categories:
        st.subheader(cat)

        df_cat = (
            df[df["Categorie"] == cat]
            .groupby("Candidat")["Points"]
            .sum()
            .reset_index()
            .sort_values(by="Points", ascending=False)
        )

        df_cat.insert(0, "Classement", range(1, len(df_cat)+1))

        st.dataframe(df_cat, use_container_width=True, hide_index=True)