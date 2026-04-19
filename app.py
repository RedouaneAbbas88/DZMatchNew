import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="DZBEST 2025/2026", layout="wide")

# ---------------------------------------------------
# HEADER LOGO
# ---------------------------------------------------
col1, col2 = st.columns([1, 6])

with col1:
    st.image("Assets/logo.PNG", width=80)

with col2:
    st.markdown("<h2 style='margin-bottom:0;'>DZBEST 2025/2026</h2>", unsafe_allow_html=True)
    st.markdown("<small>Vote officiel</small>", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------
# NAVIGATION
# ---------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "vote"

if st.button("🔐 Admin"):
    st.session_state.page = "admin"

# ---------------------------------------------------
# FONCTIONS
# ---------------------------------------------------
def clean_phone(phone):
    return "".join(filter(str.isdigit, phone))

def is_valid_phone(t):
    t = clean_phone(t)
    return t.isdigit() and len(t) == 10

def is_valid_email(e):
    return "@" in e and "." in e

# ---------------------------------------------------
# DATA
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
creds = Credentials.from_service_account_info(st.secrets["google"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")

# ---------------------------------------------------
# SAVE VOTE
# ---------------------------------------------------
def save_vote(nom, tel, email, media, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    nom_clean = nom.strip().lower()
    tel_clean = clean_phone(tel)
    email_clean = email.strip().lower()

    if not df.empty:
        df["Nom"] = df["Nom"].astype(str).str.lower()
        df["Téléphone"] = df["Téléphone"].astype(str).apply(clean_phone)
        df["Email"] = df["Email"].astype(str).str.lower()

        if (
            (df["Nom"] == nom_clean).any()
            or (df["Téléphone"] == tel_clean).any()
            or (email_clean and (df["Email"] == email_clean).any())
        ):
            return False

    for cat, selections in votes.items():
        for i, candidat in enumerate(selections, start=1):
            sheet.append_row([
                nom,
                tel_clean,
                email,
                media,
                cat,
                candidat,
                i,
                points.get(i, 0)
            ])

    return True

# ---------------------------------------------------
# DASHBOARD ADMIN
# ---------------------------------------------------
def admin_dashboard():
    data = sheet.get_all_records()

    if not data:
        st.warning("Aucun vote pour le moment")
        return

    df = pd.DataFrame(data)

    # 👥 Nombre de votants uniques
    total_voters = df["Téléphone"].nunique()
    st.markdown("## 👥 Statistiques")
    st.metric("Nombre de votants", total_voters)

    st.markdown("---")
    st.markdown("## 📊 Résultats")

    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")

    for cat in categories.keys():
        st.subheader(f"🏅 {cat}")

        df_cat = (
            df[df["Categorie"] == cat]
            .groupby("Candidat")["Points"]
            .sum()
            .reset_index()
            .sort_values(by="Points", ascending=False)
        )

        st.dataframe(df_cat, use_container_width=True, hide_index=True)

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
        selections = []

        for i in range(1, 6):
            options = ["---"] + [p["name"] for p in participants]
            selected = st.selectbox(f"{cat} - Choix {i}", options, key=f"{cat}_{i}")

            if selected != "---":
                selections.append(selected)

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
                st.success("Vote enregistré !")
            else:
                st.error("Vous avez déjà voté")

# ---------------------------------------------------
# ADMIN
# ---------------------------------------------------
if st.session_state.page == "admin":

    st.title("🔐 Admin")

    password = st.text_input("Mot de passe", type="password")

    if password == "DzBest2026!":
        admin_dashboard()

    elif password != "":
        st.error("Mot de passe incorrect")