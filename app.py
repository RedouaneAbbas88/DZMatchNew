import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# ---------------------------------------------------
# CONFIG STREAMLIT
# ---------------------------------------------------
st.set_page_config(page_title="DZBEST 2025", layout="wide")
st.title("🏆 DZBEST 2025")

# ---------------------------------------------------
# IMAGES PAR DEFAUT
# ---------------------------------------------------
DEFAULT_IMG = "Assets/default.jpg"  # image placeholder pour les candidats sans photo

# ---------------------------------------------------
# DONNÉES CATEGORIES
# ---------------------------------------------------
categories = {
    "Meilleur joueur": [
        {"name": "Adel Boulbina (PAC)", "img": "Assets/boulbina.jpg"},
        {"name": "Aymen Mahious (CRB)", "img": "Assets/mahious.jpg"},
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
        {"name": "Moustapha Zeghba (CRB)", "img": DEFAULT_IMG}
    ],
    "Meilleur entraîneur": [
        {"name": "Khaled Benyahia (MCA)", "img": DEFAULT_IMG},
        {"name": "Joseph Zinbauer (JSK)", "img": DEFAULT_IMG},
        {"name": "Sead Ramovic (CRB)", "img": DEFAULT_IMG},
        {"name": "Khereddine Madoui (CSC)", "img": DEFAULT_IMG},
        {"name": "Bilal Dziri (PAC)", "img": DEFAULT_IMG}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": DEFAULT_IMG},
        {"name": "USMA", "img": DEFAULT_IMG},
        {"name": "CSC", "img": DEFAULT_IMG},
        {"name": "CRB", "img": DEFAULT_IMG},
        {"name": "JSK", "img": DEFAULT_IMG},
        {"name": "PAC", "img": DEFAULT_IMG},
        {"name": "ESS", "img": DEFAULT_IMG}
    ]
}

max_choices = {cat: 5 for cat in categories}  # Top 5 par catégorie
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
# VALIDATION TELEPHONE ALGÉRIE
# ---------------------------------------------------
def validate_phone(phone):
    phone_clean = phone.replace(" ", "").replace("-", "")
    if not phone_clean.isdigit() and not phone_clean.startswith("+213"):
        return False, "⚠️ Le numéro doit contenir uniquement des chiffres"
    if phone_clean.startswith("0") and len(phone_clean) == 10:
        return True, ""
    elif phone_clean.startswith("+213") and len(phone_clean) == 13:
        return True, ""
    else:
        return False, "⚠️ Numéro invalide : doit être 0xxxxxxxxx ou +213xxxxxxxxx"

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
        cols = st.columns([3, 7])  # colonne petite pour image, grande pour nom
        selected_player_name = st.selectbox(
            f"Sélectionnez le joueur pour Choix #{i}",
            options=[p["name"] for p in remaining_players],
            key=f"{cat}_{i}"
        )

        # Afficher l'image à côté du nom
        p_img = next((p["img"] for p in remaining_players if p["name"] == selected_player_name), DEFAULT_IMG)
        with cols[0]:
            st.image(p_img, width=80)
        with cols[1]:
            st.write(selected_player_name)

        selections.append(selected_player_name)
        # Retire le joueur sélectionné pour le choix suivant
        remaining_players = [p for p in remaining_players if p["name"] != selected_player_name]

    vote_data[cat] = selections

# ---------------------------------------------------
# FONCTION POUR ENREGISTRER LE VOTE
# ---------------------------------------------------
def save_vote(nom, tel, media, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Vérifie double vote
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
    else:
        is_valid, msg_error = validate_phone(tel)
        if not is_valid:
            st.error(msg_error)
        elif not media.strip():
            st.error("⚠️ Entrez votre média")
        else:
            ok = save_vote(nom, tel, media, vote_data)
            if ok:
                st.success("✅ Vote enregistré !")
            else:
                st.error("⚠️ Vous avez déjà voté avec ce nom ou ce numéro de téléphone")

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
