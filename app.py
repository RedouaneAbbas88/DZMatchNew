Voici l'ancien code était bien 
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="DZBEST 2025/2026", layout="wide")

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.image("Assets/logo.PNG", width=200)
    st.markdown("<h2 style='text-align:center;'>DZBEST 2025/2026</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Vote officiel</p>", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------
# NAVIGATION
# ---------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "vote"

if st.button("🔐 Admin"):
    st.session_state.page = "admin"

# ---------------------------------------------------
# UTILS
# ---------------------------------------------------
def clean_phone(phone):
    return "".join(filter(str.isdigit, phone))

def is_valid_phone(t):
    return len(clean_phone(t)) == 10

def is_valid_email(e):
    return "@" in e and "." in e

def safe_image(path, width=120):
    if os.path.exists(path):
        st.image(path, width=width)
    else:
        st.image("Assets/default.jpg", width=width)

# ---------------------------------------------------
# DATA (NOMS EXACTS)
# ---------------------------------------------------
categories = {
    "Meilleur joueur": [
        {"name": "Mohamed Benkhemassa(MCA)", "img": "Benkhemassa.jpg"},
        {"name": "Mohamed Khacef(CRB)", "img": "khacef.jpg"},
        {"name": "Houssem Ghacha (USMA)", "img": "ghacha.jpg"},
        {"name": "Zineddine Belaid (JSK)", "img": "belaid.jpg"},
        {"name": "Merouane Zerrouki (ESS)", "img": "zerrouki.jpg"},
        {"name": "Achraf Abada (ASO/USMA)", "img": "abada.jpg"}
    ],
    "Meilleur gardien": [
        {"name": "Abdelkader Salhi (JSS)", "img": "salhi.jpg"},
        {"name": "Oussama Benbout (USMA)", "img": "benbout.jpg"},
        {"name": "Alexis Guendouz (MCA)", "img": "alexis.jpg"},
        {"name": "Farid Chaal (CRB)", "img": "chaal.jpg"},
        {"name": "Ghaya Merbah (JSK)", "img": "merbah.jpg"}
    ],
    "Meilleur entraîneur": [
        {"name": "Mounir Zegdoud (Étoile de Ben Aknoun)", "img": "mounir.jpg"},
        {"name": "Lotfi Amrouche (Akbou / Sétif)", "img": "amrouche.jpg"},
        {"name": "Sead Ramović (CRB)", "img": "sead.jpg"},
        {"name": "Abdelkader Amrani (JSS)", "img": "amrani.jpg"},
        {"name": "Chérif El Ouazzani (MCO)", "img": "cherif.jpg"}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": "MCA.jpg"},
        {"name": "USMA", "img": "USMA.jpg"},
        {"name": "MCO", "img": "MCO.jpg"},
        {"name": "CRB", "img": "CRB.jpg"},
        {"name": "JSK", "img": "JSK.jpg"},
        {"name": "O. AKBOU", "img": "akbou.jpg"},
        {"name": "ESBA", "img": "ESBA.jpg"}
    ],
    "Meilleur joueur étranger": [
        {"name": "Che Malone (USMA)", "img": "malone.jpg"},
        {"name": "Arthur Bada (JSK)", "img": "bada.jpg"},
        {"name": "Matuti (USMK)", "img": "matuti.jpg"},
        {"name": "Kipre Junior (MCA)", "img": "Kipre.jpg"},
        {"name": "Mohamed Ali Ben Hamouda (CRB)", "img": "benhamouda.jpg"}
    ]
}

points = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# ---------------------------------------------------
# GOOGLE SHEETS
# ---------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_resource
def connect_sheet():
    creds = Credentials.from_service_account_info(st.secrets["google"], scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")

sheet = connect_sheet()

@st.cache_data(ttl=60)
def load_data():
    return sheet.get_all_records()

# ---------------------------------------------------
# SAVE VOTE
# ---------------------------------------------------
def save_vote(nom, tel, email, media, votes):
    try:
        df = pd.DataFrame(load_data())

        tel_clean = clean_phone(tel)

        if not df.empty:
            df["Téléphone"] = df["Téléphone"].astype(str).apply(clean_phone)

            if (df["Téléphone"] == tel_clean).any():
                return False

        rows = []

        for cat, selections in votes.items():
            for i, candidat in enumerate(selections, start=1):
                rows.append([
                    nom,
                    tel_clean,
                    email,
                    media,
                    cat,
                    candidat,
                    i,
                    points.get(i, 0)
                ])

        sheet.append_rows(rows)
        load_data.clear()

        return True

    except Exception:
        st.error("⚠️ Erreur serveur, réessayez")
        return False

# ---------------------------------------------------
# RESULTS
# ---------------------------------------------------
def show_results():
    df = pd.DataFrame(load_data())

    if df.empty:
        st.warning("Pas encore de résultats")
        return

    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")
    df["Téléphone"] = df["Téléphone"].astype(str).apply(clean_phone)

    df_valid = df[df["Téléphone"].str.len() == 10]
    nb_votants = df_valid["Téléphone"].drop_duplicates().count()

    st.markdown(f"### 👥 Nombre de votants : {nb_votants}")

    for cat, participants in categories.items():

        st.subheader(f"🏅 {cat}")

        df_cat = (
            df[df["Categorie"] == cat]
            .groupby("Candidat")["Points"]
            .sum()
            .reset_index()
            .sort_values(by="Points", ascending=False)
        )

        # ✅ MODIFICATION UNIQUEMENT ICI → TOP 5
        df_cat = df_cat.head(5).reset_index(drop=True)
        df_cat.index = df_cat.index + 1

        cols = st.columns(3)
        top3 = df_cat.head(3)

        for i, (_, row) in enumerate(top3.iterrows()):
            name = row["Candidat"]
            pts = row["Points"]

            img = next((p["img"] for p in participants if p["name"] == name), "default.jpg")

            with cols[i]:
                safe_image(f"Assets/{img}", 120)
                st.markdown(f"**#{i+1} {name}**")
                st.write(f"{pts} points")

        st.dataframe(df_cat, use_container_width=True)

# ---------------------------------------------------
# PAGE VOTE
# ---------------------------------------------------
if st.session_state.page == "vote":

    nom = st.text_input("📝 Nom et prénom")
    tel = st.text_input("📞 Téléphone")
    email = st.text_input("📧 Email (optionnel)")
    media = st.text_input("📸 Média/Fonction")

    vote_data = {}

    for cat, participants in categories.items():
        st.subheader(f"🏅 {cat}")

        remaining = participants.copy()
        selections = []

        for i in range(1, 6):
            options = ["---"] + [p["name"] for p in remaining]
            choice = st.selectbox(f"{cat} - Choix {i}", options, key=f"{cat}_{i}")

            if choice != "---":
                selections.append(choice)
                remaining = [p for p in remaining if p["name"] != choice]

                img = next((p["img"] for p in participants if p["name"] == choice), "default.jpg")

                col1, col2 = st.columns([1, 5])
                with col1:
                    safe_image(f"Assets/{img}", 80)
                with col2:
                    st.write(choice)

        vote_data[cat] = selections

    if st.button("✅ Envoyer mon vote"):

        if not nom.strip():
            st.error("Nom requis")

        elif not is_valid_phone(tel):
            st.error("Téléphone invalide")

        elif email.strip() and not is_valid_email(email):
            st.error("Email invalide")

        elif not media.strip():
            st.error("Média requis")

        else:
            ok = save_vote(nom, tel, email, media, vote_data)

            if ok:
                st.session_state.page = "results"
                st.rerun()
            else:
                st.error("❌ Ce numéro a déjà voté")

# ---------------------------------------------------
# RESULTS PAGE
# ---------------------------------------------------
if st.session_state.page == "results":
    st.success("✅ Vote enregistré !")
    show_results()

# ---------------------------------------------------
# ADMIN
# ---------------------------------------------------
if st.session_state.page == "admin":

    st.title("🔐 Admin")

    password = st.text_input("Mot de passe", type="password")

    if password == "123456":
        show_results()

    elif password != "":
        st.error("Mot de passe incorrect")