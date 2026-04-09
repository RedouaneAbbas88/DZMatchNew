import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="DZBEST 2025", layout="wide")
st.title("🏆 DZBEST 2025")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_img(filename):
    return os.path.join(BASE_DIR, "Assets", filename)

DEFAULT_IMG = "default.jpg"

# -------------------------
# CATEGORIES
# -------------------------
categories = {
    "Meilleur joueur": [
        {"name": "Adel Boulbina (PAC)", "img": "boulbina.jpg"},
        {"name": "Aymen Mahious (CRB)", "img": "mahious.jpg"},
        {"name": "Abderrahmane Meziane (CRB)", "img": DEFAULT_IMG},
        {"name": "Ibrahim Dib (CSC)", "img": DEFAULT_IMG},
        {"name": "Salim Boukhenchouch (USMA)", "img": DEFAULT_IMG},
        {"name": "Larbi Tabti (MCA)", "img": DEFAULT_IMG},
        {"name": "Mehdi Boudjamaa (JSK)", "img": DEFAULT_IMG}
    ],
    "Meilleur gardien": [
        {"name": "Oussama Benbout (USMA)", "img": DEFAULT_IMG},
        {"name": "Zakaria Bouhalfaya (CSC)", "img": DEFAULT_IMG},
        {"name": "Abderrahmane Medjadel (ASO)", "img": DEFAULT_IMG},
        {"name": "Tarek Boussder (ESS)", "img": DEFAULT_IMG},
        {"name": "Abdelkader Salhi (MCEB)", "img": DEFAULT_IMG},
        {"name": "Moustapha Zeghba (CRB)", "img": DEFAULT_IMG},
        {"name": "Hadid Mohamed (JSK)", "img": DEFAULT_IMG},
        {"name": "Ramdane Abdelatif (MCA)", "img": DEFAULT_IMG}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": DEFAULT_IMG},
        {"name": "USMA", "img": DEFAULT_IMG},
        {"name": "CSC", "img": DEFAULT_IMG},
        {"name": "CRB", "img": DEFAULT_IMG},
        {"name": "JSK", "img": DEFAULT_IMG},
        {"name": "PAC", "img": DEFAULT_IMG},
        {"name": "ESS", "img": DEFAULT_IMG}
    ],
    "Meilleur entraîneur": [
        {"name": "Khaled Benyahia (MCA)", "img": DEFAULT_IMG},
        {"name": "Joseph Zinbauer (JSK)", "img": DEFAULT_IMG},
        {"name": "Sead Ramovic (CRB)", "img": DEFAULT_IMG},
        {"name": "Khereddine Madoui (CSC)", "img": DEFAULT_IMG},
        {"name": "Bilal Dziri (PAC)", "img": DEFAULT_IMG}
    ]
}

max_choices = {cat: 5 for cat in categories}
points = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# -------------------------
# GOOGLE SHEETS
# -------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")

# -------------------------
# INFOS VOTANT
# -------------------------
nom = st.text_input("📝 Nom et prénom")
tel = st.text_input("📞 Téléphone")
media = st.text_input("📸 Média")

# -------------------------
# VOTE
# -------------------------
vote_data = {}

for cat, participants in categories.items():
    st.subheader(f"🏅 {cat}")
    selections = []

    for i in range(1, max_choices[cat] + 1):
        options = [p["name"] for p in participants if p["name"] not in selections]

        # --- COLONNES (PC) / Responsive mobile automatique ---
        col1, col2 = st.columns([4, 1], gap="small")
        with col1:
            choice = st.selectbox(f"{cat} - Choix #{i}", ["-- Choisir --"] + options, key=f"{cat}_{i}")

        with col2:
            if choice != "-- Choisir --":
                for p in participants:
                    if p["name"] == choice:
                        img_path = get_img(p["img"])
                        if os.path.exists(img_path):
                            st.image(img_path, width=40)
                        else:
                            st.image(get_img(DEFAULT_IMG), width=50)

        if choice != "-- Choisir --":
            selections.append(choice)

    vote_data[cat] = selections

# -------------------------
# SAVE
# -------------------------
def save_vote(nom, tel, media, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        if nom in df.get("Nom", []).values:
            return False
        if tel in df.get("Téléphone", []).values:
            return False

    rows = []
    for cat, selections in votes.items():
        for i, candidat in enumerate(selections, start=1):
            rows.append([nom, tel, media, cat, candidat, i, points.get(i, 0)])

    for r in rows:
        sheet.append_row(r)

    return True

# -------------------------
# ENVOI
# -------------------------
if st.button("✅ Envoyer mon vote"):
    if not nom or not tel or not media:
        st.error("⚠️ Remplir tous les champs")
    else:
        ok = save_vote(nom, tel, media, vote_data)
        if ok:
            st.success("✅ Vote enregistré !")
        else:
            st.error("⚠️ Vous avez déjà voté")

# -------------------------
# RESULTATS
# -------------------------
st.header("📊 Classements")
data = sheet.get_all_records()

if data:
    df = pd.DataFrame(data)
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")

    for cat in categories:
        st.subheader(cat)
        df_cat = (
            df[df["Categorie"] == cat]
            .groupby("Candidat")["Points"].sum()
            .reset_index()
            .sort_values(by="Points", ascending=False)
        )
        df_cat.insert(0, "Classement", range(1, len(df_cat)+1))
        st.dataframe(df_cat, use_container_width=True, hide_index=True)
