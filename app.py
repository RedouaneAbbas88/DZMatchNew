import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import re
import os

# ---------------------------------------------------
# CONFIG STREAMLIT
# ---------------------------------------------------
st.set_page_config(page_title="DZBEST 2025", layout="wide")
st.title("🏆 DZBEST 2025")

# ---------------------------------------------------
# IMAGE PAR DÉFAUT
# ---------------------------------------------------
DEFAULT_IMG = "Assets/default.jpg"  # Image par défaut si la photo n'existe pas

# ---------------------------------------------------
# CATEGORIES AVEC PHOTOS (seulement 2 photos réelles pour test)
# ---------------------------------------------------
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
        {"name": "Zakaria Bouhalfaya (CSC)", "img": DEFAULT_IMG}
    ],
    "Meilleur entraîneur": [
        {"name": "Khaled Benyahia (MCA)", "img": DEFAULT_IMG},
        {"name": "Joseph Zinbauer (JSK)", "img": DEFAULT_IMG}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": DEFAULT_IMG},
        {"name": "USMA", "img": DEFAULT_IMG}
    ]
}

max_choices = {cat: 5 for cat in categories}  # max 5 choix par catégorie
points = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# ---------------------------------------------------
# GOOGLE SHEETS
# ---------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
try:
    creds = Credentials.from_service_account_info(st.secrets["google"], scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")
except Exception as e:
    st.error("❌ Impossible de se connecter à Google Sheet. Vérifiez la clé et les permissions.")
    st.stop()

# ---------------------------------------------------
# INFOS VOTANT
# ---------------------------------------------------
nom = st.text_input("📝 Nom et prénom")
tel = st.text_input("📞 Numéro de téléphone (9 chiffres)")
media = st.text_input("📸 Média")

# Validation téléphone
def is_valid_phone(number):
    return bool(re.fullmatch(r"\d{9}", number.strip()))

# ---------------------------------------------------
# VOTE PAR CLASSE
# ---------------------------------------------------
vote_data = {}

for cat, participants in categories.items():
    st.subheader(f"🏅 {cat}")
    remaining_players = participants.copy()
    selections = []

    for i in range(1, max_choices[cat]+1):
        st.markdown(f"**Choix #{i} :**")

        # Dropdown avec noms seulement, initialement vide
        options = [""] + [p["name"] for p in remaining_players]
        selected_name = st.selectbox(f"Classe #{i} pour {cat}", options, key=f"{cat}_{i}")

        if selected_name and selected_name != "":
            selections.append(selected_name)
            # Retire le joueur sélectionné pour ne plus l'afficher
            remaining_players = [p for p in remaining_players if p["name"] != selected_name]

            # Affiche la photo du joueur choisi
            p_img = next((p["img"] for p in participants if p["name"] == selected_name), DEFAULT_IMG)
            if not os.path.isfile(p_img):
                p_img = DEFAULT_IMG
            st.image(p_img, width=100)

    vote_data[cat] = selections

# ---------------------------------------------------
# FONCTION POUR ENREGISTRER LE VOTE
# ---------------------------------------------------
def save_vote(nom, tel, media, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        if "Téléphone" in df.columns and tel in df["Téléphone"].values:
            return False  # déjà voté pour ce numéro

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
    elif not tel.strip() or not is_valid_phone(tel):
        st.error("⚠️ Numéro de téléphone invalide. Doit contenir 9 chiffres.")
    elif not media.strip():
        st.error("⚠️ Entrez votre média")
    else:
        ok = save_vote(nom, tel, media, vote_data)
        if ok:
            st.success("✅ Vote enregistré !")
        else:
            st.error("⚠️ Ce numéro de téléphone a déjà voté.")

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
