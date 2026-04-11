import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------
# CONFIG STREAMLIT
# ---------------------------------------------------
st.set_page_config(page_title="DZBEST 2025", layout="wide")
st.title("🏆 DZBEST 2025")

# ---------------------------------------------------
# NAVIGATION
# ---------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "vote"

# ---------------------------------------------------
# DONNÉES
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
        {"name": "Mounir Zegdoud (Étoile de Ben Aknoun)", "img": "defqult.jpg"},
        {"name": "Lotfi Amrouche (Akbou / Sétif)", "img": "defqult.jpg"},
        {"name": "Sead Ramović (CRB)", "img": "defqult.jpg"},
        {"name": "Abdelkader Amrani (JSS)", "img": "defqult.jpg"},
        {"name": "Chérif El Ouazzani (MCO)", "img": "defqult.jpg"}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": "defqult.jpg"},
        {"name": "USMA", "img": "defqult.jpg"},
        {"name": "MCO", "img": "defqult.jpg"},
        {"name": "CRB", "img": "defqult.jpg"},
        {"name": "JSK", "img": "defqult.jpg"},
        {"name": "O. Akbou", "img": "defqult.jpg"},
        {"name": "ESBA", "img": "defqult.jpg"}
    ]
}

max_choices = {cat: 5 for cat in categories}
points = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# ---------------------------------------------------
# GOOGLE SHEETS
# ---------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")

# ---------------------------------------------------
# PAGE VOTE
# ---------------------------------------------------
if st.session_state.page == "vote":

    nom = st.text_input("📝 Nom et prénom")
    tel = st.text_input("📞 Téléphone")
    media = st.text_input("📸 Média")

    def is_valid_phone(t):
        return t.isdigit() and len(t) == 9

    vote_data = {}

    for cat, participants in categories.items():
        st.subheader(f"🏅 {cat}")
        remaining_players = participants.copy()
        selections = []

        for i in range(1, max_choices[cat] + 1):
            options = ["--- Sélectionnez ---"] + [p["name"] for p in remaining_players]
            selected = st.selectbox(f"{cat} - Choix {i}", options, key=f"{cat}_{i}")

            if selected != "--- Sélectionnez ---":
                selections.append(selected)
                remaining_players = [p for p in remaining_players if p["name"] != selected]

        vote_data[cat] = selections

    def save_vote(nom, tel, media, votes):
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        if not df.empty and "Téléphone" in df.columns:
            if tel in df["Téléphone"].values:
                return False

        rows = []
        for cat, selections in votes.items():
            for i, candidat in enumerate(selections, start=1):
                rows.append([nom, tel, media, cat, candidat, i, points.get(i, 0)])

        for r in rows:
            sheet.append_row(r)

        return True

    if st.button("✅ Envoyer mon vote"):

        if not nom:
            st.error("Entrez votre nom")
        elif not is_valid_phone(tel):
            st.error("Numéro invalide")
        elif not media:
            st.error("Entrez votre média")
        else:
            ok = save_vote(nom, tel, media, vote_data)

            if ok:
                st.session_state.page = "results"
                st.rerun()
            else:
                st.error("Vous avez déjà voté")

# ---------------------------------------------------
# PAGE RESULTATS
# ---------------------------------------------------
if st.session_state.page == "results":

    st.success("Vote enregistré !")

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
                .head(5)
            )

            df_cat.insert(0, "Classement", range(1, len(df_cat) + 1))

            st.dataframe(df_cat, use_container_width=True, hide_index=True)