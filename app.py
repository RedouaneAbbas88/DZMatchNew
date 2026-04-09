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
# CHEMIN DES IMAGES
# ---------------------------------------------------
ASSETS_PATH = "Assets/"
DEFAULT_IMG = "default.jpg"

# ---------------------------------------------------
# DONNÉES CATEGORIES AVEC PHOTOS LOCALES
# ---------------------------------------------------
categories = {
    "Meilleur joueur": [
        {"name": "Adel Boulbina (PAC)", "img": "boulbina.jpg"},
        {"name": "Aymen Mahious (CRB)", "img": "mahious.jpg"},
        {"name": "Abderrahmane Meziane (CRB)", "img": "defqult.jpg"},
        {"name": "Ibrahim Dib (CSC)", "img": "defqult.jpg"},
        {"name": "Salim Boukhenchouch (USMA)", "img": "defqult.jpg"},
        {"name": "Larbi Tabti (MCA)", "img": "defqult.jpg"},
        {"name": "Mehdi Boudjamaa (JSK)", "img": "defqult.jpg"}
    ],
    "Meilleur gardien": [
        {"name": "Oussama Benbout (USMA)", "img": "defqult.jpg"},
        {"name": "Zakaria Bouhalfaya (CSC)", "img": "defqult.jpg"},
        {"name": "Abderrahmane Medjadel (ASO)", "img": "defqult.jpg"},
        {"name": "Tarek Boussder (ESS)", "img": "defqult.jpg"},
        {"name": "Abdelkader Salhi (MCEB)", "img": "defqult.jpg"},
        {"name": "Moustapha Zeghba (CRB)", "img": "defqult.jpg"}
    ],
    "Meilleur entraîneur": [
        {"name": "Khaled Benyahia (MCA)", "img": "defqult.jpg"},
        {"name": "Joseph Zinbauer (JSK)", "img": "defqult.jpg"},
        {"name": "Sead Ramovic (CRB)", "img": "defqult.jpg"},
        {"name": "Khereddine Madoui (CSC)", "img": "defqult.jpg"},
        {"name": "Bilal Dziri (PAC)", "img": "defqult.jpg"}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": "defqult.jpg"},
        {"name": "USMA", "img": "defqult.jpg"},
        {"name": "CSC", "img": "defqult.jpg"},
        {"name": "CRB", "img": "defqult.jpg"},
        {"name": "JSK", "img": "defqult.jpg"},
        {"name": "PAC", "img": "defqult.jpg"},
        {"name": "ESS", "img": "defqult.jpg"}
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
# INFOS VOTANT
# ---------------------------------------------------
nom = st.text_input("📝 Nom et prénom")
tel = st.text_input("📞 Téléphone (9 chiffres)")
media = st.text_input("📸 Média")

# ---------------------------------------------------
# VALIDATION DU NUMERO DE TELEPHONE
# ---------------------------------------------------
def is_valid_phone(number):
    return number.isdigit() and len(number) == 9

# ---------------------------------------------------
# VOTE
# ---------------------------------------------------
vote_data = {}

for cat, participants in categories.items():
    st.subheader(f"🏅 {cat}")
    remaining = participants.copy()
    selections = [None] * max_choices[cat]  # vide par défaut

    for i in range(max_choices[cat]):
        # Crée la liste déroulante des candidats encore disponibles
        options = [p["name"] for p in remaining]
        selected = st.selectbox(f"Choix #{i+1} pour {cat} :", [""] + options, key=f"{cat}_{i}")

        if selected != "" and selected not in selections:
            selections[i] = selected
            # Supprime le joueur sélectionné pour ne plus l’afficher
            remaining = [p for p in remaining if p["name"] != selected]

        # Affiche la photo du choix déjà fait
        if selections[i]:
            p_img_name = next((p["img"] for p in participants if p["name"] == selections[i]), DEFAULT_IMG)
            p_img_path = ASSETS_PATH + p_img_name
            st.image(p_img_path, width=80, caption=selections[i])

    vote_data[cat] = [s for s in selections if s]

# ---------------------------------------------------
# ENREGISTRER LE VOTE
# ---------------------------------------------------
def save_vote(nom, tel, media, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Vérifie si le votant existe déjà
    if not df.empty:
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
# BOUTON ENVOI
# ---------------------------------------------------
if st.button("✅ Envoyer mon vote"):

    if not nom.strip():
        st.error("⚠️ Entrez votre nom")
    elif not is_valid_phone(tel.strip()):
        st.error("⚠️ Entrez un numéro valide de 9 chiffres")
    elif not media.strip():
        st.error("⚠️ Entrez votre média")
    else:
        ok = save_vote(nom.strip(), tel.strip(), media.strip(), vote_data)
        if ok:
            st.success("✅ Vote enregistré !")
        else:
            st.error("⚠️ Ce numéro de téléphone a déjà voté")

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
