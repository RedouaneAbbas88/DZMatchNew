import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="DZBEST 2025", layout="wide")
st.title("🏆 DZBEST 2025")

# ---------------------------------------------------
# CHEMIN ABSOLU (IMPORTANT)
# ---------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_img_path(filename):
    return os.path.join(BASE_DIR, "Assets", filename)

# ---------------------------------------------------
# DONNÉES (IMAGES DANS Assets/)
# ---------------------------------------------------
categories = {
    "Meilleur joueur": [
        {"name": "Adel Boulbina (PAC)", "img": "boulbina.jpg"},
        {"name": "Aymen Mahious (CRB)", "img": "mahious.jpg"}
    ],
    "Meilleur gardien": [
        {"name": "Oussama Benbout (USMA)", "img": "boulbina.jpg"}  # test
    ],
    "Meilleur entraîneur": [
        {"name": "Khaled Benyahia (MCA)", "img": "mahious.jpg"}  # test
    ],
    "Meilleur club": [
        {"name": "MCA", "img": "boulbina.jpg"}  # test
    ]
}

max_choices = {cat: 2 for cat in categories}  # 2 pour test
points = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# ---------------------------------------------------
# GOOGLE SHEETS
# ---------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")

# ---------------------------------------------------
# INFOS VOTANT
# ---------------------------------------------------
nom = st.text_input("📝 Nom et prénom")
tel = st.text_input("📞 Téléphone")
media = st.text_input("📸 Média")

# ---------------------------------------------------
# VOTE PAR CARTES (AVEC PHOTOS)
# ---------------------------------------------------
vote_data = {}

for cat, participants in categories.items():
    st.subheader(f"🏅 {cat}")

    remaining = participants.copy()
    selections = []

    for i in range(1, max_choices[cat] + 1):

        st.markdown(f"### Choix #{i}")
        cols = st.columns(len(remaining))

        selected = None

        for idx, p in enumerate(remaining):
            with cols[idx]:
                img_path = get_img_path(p["img"])

                # Vérification image
                if os.path.exists(img_path):
                    st.image(img_path, width=100)
                else:
                    st.warning(f"Image manquante: {p['img']}")

                st.write(p["name"])

                if st.button("Choisir", key=f"{cat}_{i}_{p['name']}"):
                    selected = p["name"]

        if selected:
            selections.append(selected)
            remaining = [p for p in remaining if p["name"] != selected]

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

# ---------------------------------------------------
# ENVOI
# ---------------------------------------------------
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
