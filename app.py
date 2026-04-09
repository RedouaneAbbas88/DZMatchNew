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
# DONNÉES CATEGORIES AVEC PHOTOS LOCALES
# ---------------------------------------------------
categories = {
    "Meilleur joueur": [
        {"name": "Adel Boulbina (PAC)", "img": "Assets/candidates/boulbina.jpg"},
        {"name": "Aymen Mahious (CRB)", "img": "Assets/candidates/mahious.jpg"},
        {"name": "Abderrahmane Meziane (CRB)", "img": "Assets/candidates/meziane.jpg"},
        {"name": "Ibrahim Dib (CSC)", "img": "Assets/candidates/dib.jpg"},
        {"name": "Salim Boukhenchouch (USMA)", "img": "Assets/candidates/boukhenchouch.jpg"},
        {"name": "Larbi Tabti (MCA)", "img": "Assets/candidates/tabti.jpg"},
        {"name": "Mehdi Boudjamaa (JSK)", "img": "Assets/candidates/boudjamaa.jpg"}
    ],
    "Meilleur gardien": [
        {"name": "Oussama Benbout (USMA)", "img": "Assets/candidates/benbout.jpg"},
        {"name": "Zakaria Bouhalfaya (CSC)", "img": "Assets/candidates/bouhalfaya.jpg"},
        {"name": "Abderrahmane Medjadel (ASO)", "img": "Assets/candidates/medjadel.jpg"},
        {"name": "Tarek Boussder (ESS)", "img": "Assets/candidates/boussder.jpg"},
        {"name": "Abdelkader Salhi (MCEB)", "img": "Assets/candidates/salhi.jpg"},
        {"name": "Moustapha Zeghba (CRB)", "img": "Assets/candidates/zeghba.jpg"}
    ],
    "Meilleur entraîneur": [
        {"name": "Khaled Benyahia (MCA)", "img": "Assets/candidates/benyahia.jpg"},
        {"name": "Joseph Zinbauer (JSK)", "img": "Assets/candidates/zinbauer.jpg"},
        {"name": "Sead Ramovic (CRB)", "img": "Assets/candidates/ramovic.jpg"},
        {"name": "Khereddine Madoui (CSC)", "img": "Assets/candidates/madoui.jpg"},
        {"name": "Bilal Dziri (PAC)", "img": "Assets/candidates/dziri.jpg"}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": "Assets/candidates/mca.jpg"},
        {"name": "USMA", "img": "Assets/candidates/usma.jpg"},
        {"name": "CSC", "img": "Assets/candidates/csc.jpg"},
        {"name": "CRB", "img": "Assets/candidates/crb.jpg"},
        {"name": "JSK", "img": "Assets/candidates/jsk.jpg"},
        {"name": "PAC", "img": "Assets/candidates/pac.jpg"},
        {"name": "ESS", "img": "Assets/candidates/ess.jpg"}
    ]
}

# ---------------------------------------------------
# NOMBRE MAX DE CHOIX ET POINTS
# ---------------------------------------------------
max_choices = {"Meilleur joueur": 5, "Meilleur gardien": 5, "Meilleur entraîneur": 5, "Meilleur club": 5}
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
# VOTE PAR CLASSE AVEC PHOTOS
# ---------------------------------------------------
vote_data = {}
st.header("Sélection des candidats")

for cat, participants in categories.items():
    st.subheader(f"🏅 {cat}")
    remaining = participants.copy()
    selections = []

    for i in range(1, max_choices[cat]+1):
        st.markdown(f"**Choix #{i} :**")
        col1, col2 = st.columns([2, 5])
        # Liste déroulante vide par défaut
        options = [p["name"] for p in remaining]
        selected_name = col1.selectbox("Sélectionnez", [""] + options, key=f"{cat}_{i}")

        # Affichage de la photo à côté
        if selected_name:
            p_img = next((p["img"] for p in remaining if p["name"] == selected_name), None)
            if p_img:
                col2.image(p_img, width=100)
            selections.append(selected_name)
            # Retirer le candidat choisi
            remaining = [p for p in remaining if p["name"] != selected_name]

    vote_data[cat] = selections

# ---------------------------------------------------
# FONCTION POUR ENREGISTRER LE VOTE
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
# BOUTON ENVOI VOTE
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
        df_cat = df[df["Categorie"] == cat].groupby("Candidat")["Points"].sum().reset_index()
        df_cat = df_cat.sort_values(by="Points", ascending=False)
        df_cat.insert(0, "Classement", range(1, len(df_cat)+1))
        st.dataframe(df_cat, use_container_width=True, hide_index=True)
