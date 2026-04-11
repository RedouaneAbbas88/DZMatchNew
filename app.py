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
# NAVIGATION
# ---------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "vote"

# ---------------------------------------------------
# DATA
# ---------------------------------------------------
categories = {
    "Meilleur joueur": [
        {"name": "Zineddine Ferhat (MCA)", "img": "boulbina.jpg"},
        {"name": "Mohamed Khacef(CRB)", "img": "mahious.jpg"},
        {"name": "Houssem Ghacha (USMA)", "img": "defqult.jpg"},
        {"name": "Zineddine Belaid (JSK)", "img": "defqult.jpg"},
        {"name": "Merouane Zerrouki (ESS)", "img": "defqult.jpg"},
        {"name": "Achraf Abada (ASO/USMA)", "img": "defqult.jpg"}
    ],
    "Meilleur gardien": [
        {"name": "Abdelkader Salhi (JSS)", "img": "defqult.jpg"},
        {"name": "Oussama Benbout (USMA)", "img": "defqult.jpg"},
        {"name": "Alexis Guendouz (MCA)", "img": "defqult.jpg"},
        {"name": "Farid Chaal (CRB)", "img": "defqult.jpg"},
        {"name": "Ghaya Merbah (JSK)", "img": "defqult.jpg"}
    ],
    "Meilleur entraîneur": [
        {"name": "Mounir Zegdoud", "img": "defqult.jpg"},
        {"name": "Lotfi Amrouche", "img": "defqult.jpg"},
        {"name": "Sead Ramović", "img": "defqult.jpg"},
        {"name": "Abdelkader Amrani", "img": "defqult.jpg"},
        {"name": "Chérif El Ouazzani", "img": "defqult.jpg"}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": "defqult.jpg"},
        {"name": "USMA", "img": "defqult.jpg"},
        {"name": "CRB", "img": "defqult.jpg"},
        {"name": "JSK", "img": "defqult.jpg"},
        {"name": "MCO", "img": "defqult.jpg"}
    ]
}

max_choices = {cat: 5 for cat in categories}
points = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# ---------------------------------------------------
# GOOGLE SHEETS
# ---------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["google"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")

# ---------------------------------------------------
# PAGE VOTE
# ---------------------------------------------------
if st.session_state.page == "vote":

    nom = st.text_input("Nom et prénom")
    tel = st.text_input("Téléphone")
    media = st.text_input("Média")

    vote_data = {}

    for cat, participants in categories.items():
        st.subheader(cat)
        remaining = participants.copy()
        selections = []

        for i in range(1, 6):
            options = ["---"] + [p["name"] for p in remaining]
            choice = st.selectbox(f"{cat} - Choix {i}", options, key=f"{cat}_{i}")

            if choice != "---":
                selections.append(choice)
                remaining = [p for p in remaining if p["name"] != choice]

        vote_data[cat] = selections

    def save_vote():
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        if not df.empty and tel in df["Téléphone"].values:
            return False

        for cat, selections in vote_data.items():
            for i, c in enumerate(selections, start=1):
                sheet.append_row([nom, tel, media, cat, c, i, points[i]])

        return True

    if st.button("Envoyer"):

        if not nom or not tel or not media:
            st.error("Remplir tous les champs")
        else:
            if save_vote():
                st.session_state.page = "results"
                st.rerun()
            else:
                st.error("Vous avez déjà voté")

# ---------------------------------------------------
# PAGE RESULTATS
# ---------------------------------------------------
if st.session_state.page == "results":

    st.success("Vote enregistré")

    data = sheet.get_all_records()

    if data:
        df = pd.DataFrame(data)
        df["Points"] = pd.to_numeric(df["Points"], errors="coerce")

        for cat, participants in categories.items():

            st.subheader(cat)

            df_cat = (
                df[df["Categorie"] == cat]
                .groupby("Candidat")["Points"]
                .sum()
                .reset_index()
                .sort_values(by="Points", ascending=False)
            )

            top5 = df_cat.head(5)

            # 🏆 PODIUM
            st.markdown("### 🥇 Podium")

            podium = top5.head(3)
            cols = st.columns(3)

            for i, (_, row) in enumerate(podium.iterrows()):
                name = row["Candidat"]
                pts = row["Points"]

                img = next((p["img"] for p in participants if p["name"] == name), "defqult.jpg")

                with cols[i]:
                    st.image(f"Assets/{img}", width=120)
                    st.markdown(f"**#{i+1} {name}**")
                    st.write(f"{pts} pts")

            # 📊 TABLE
            st.markdown("### Classement")

            top5 = top5.copy()
            top5.insert(0, "Rank", range(1, len(top5)+1))

            st.dataframe(top5, use_container_width=True)