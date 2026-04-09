import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

st.set_page_config(page_title="DZBEST 2025", layout="wide")
st.title("🏆 DZBEST 2025")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------- Fonctions -----------------
def get_img_path(filename):
    path = os.path.join(BASE_DIR, "Assets", filename)
    return path if os.path.exists(path) else os.path.join(BASE_DIR, "Assets", "default.jpg")

# ----------------- Données -----------------
categories = {
    "Meilleur joueur": [
        {"name": "Adel Boulbina (PAC)", "img": "boulbina.jpg"},
        {"name": "Aymen Mahious (CRB)", "img": "mahious.jpg"},
        {"name": "Abderrahmane Meziane (CRB)", "img": "default.jpg"},
        {"name": "Ibrahim Dib (CSC)", "img": "default.jpg"},
        {"name": "Salim Boukhenchouch (USMA)", "img": "default.jpg"},
        {"name": "Larbi Tabti (MCA)", "img": "default.jpg"},
        {"name": "Mehdi Boudjamaa (JSK)", "img": "default.jpg"}
    ],
    "Meilleur gardien": [
        {"name": "Oussama Benbout (USMA)", "img": "default.jpg"},
        {"name": "Zakaria Bouhalfaya (CSC)", "img": "default.jpg"},
        {"name": "Abderrahmane Medjadel (ASO)", "img": "default.jpg"},
        {"name": "Tarek Boussder (ESS)", "img": "default.jpg"},
        {"name": "Abdelkader Salhi (MCEB)", "img": "default.jpg"},
        {"name": "Moustapha Zeghba (CRB)", "img": "default.jpg"}
    ],
    "Meilleur entraîneur": [
        {"name": "Khaled Benyahia (MCA)", "img": "default.jpg"},
        {"name": "Joseph Zinbauer (JSK)", "img": "default.jpg"},
        {"name": "Sead Ramovic (CRB)", "img": "default.jpg"},
        {"name": "Khereddine Madoui (CSC)", "img": "default.jpg"},
        {"name": "Bilal Dziri (PAC)", "img": "default.jpg"}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": "default.jpg"},
        {"name": "USMA", "img": "default.jpg"},
        {"name": "CSC", "img": "default.jpg"},
        {"name": "CRB", "img": "default.jpg"},
        {"name": "JSK", "img": "default.jpg"},
        {"name": "PAC", "img": "default.jpg"},
        {"name": "ESS", "img": "default.jpg"}
    ]
}

MAX_TOP = 5
points = {1:5, 2:4, 3:3, 4:2, 5:1}

# ----------------- Infos votant -----------------
nom = st.text_input("📝 Nom et prénom")
tel = st.text_input("📞 Téléphone")
media = st.text_input("📸 Média")

# ----------------- Google Sheets -----------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")

# ----------------- Vote -----------------
vote_data = {}

for cat, items in categories.items():
    st.header(cat)
    remaining = items.copy()
    selections = []
    
    for rank in range(1, min(MAX_TOP, len(items))+1):
        st.subheader(f"Classe {rank}")
        options = [p["name"] for p in remaining]
        selected_name = st.selectbox(f"Choisir pour Classe {rank} :", options, key=f"{cat}_{rank}")
        
        selected_player = next((p for p in remaining if p["name"] == selected_name), None)
        if selected_player:
            selections.append(selected_player)
            st.image(get_img_path(selected_player["img"]), width=80)
            remaining = [p for p in remaining if p["name"] != selected_name]
    
    vote_data[cat] = selections

# ----------------- Sauvegarder le vote -----------------
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
        for i, p in enumerate(selections, start=1):
            rows.append([nom, tel, media, cat, p["name"], i, points.get(i, 0)])
    
    for r in rows:
        sheet.append_row(r)
    return True

# ----------------- Bouton Envoi -----------------
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

# ----------------- Résultats -----------------
st.header("📊 Classements")
data = sheet.get_all_records()
if data:
    df = pd.DataFrame(data)
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")
    
    for cat in categories:
        st.subheader(cat)
        df_cat = df[df["Categorie"] == cat].groupby("Candidat")["Points"].sum().reset_index()
        df_cat = df_cat.sort_values(by="Points", ascending=False)
        df_cat.insert(0, "Classement", range(1, len(df_cat)+1))
        st.dataframe(df_cat, use_container_width=True, hide_index=True)
