import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# -----------------------------
# CONFIGURATION STREAMLIT
# -----------------------------
st.set_page_config(page_title="DZBEST 2025", layout="wide")
st.title("🏆 DZBEST 2025")

# -----------------------------
# IMAGE PAR DEFAUT
# -----------------------------
DEFAULT_IMG = "default.jpg"  # mettre une image par défaut dans le dossier Assets

# -----------------------------
# LISTE DES CANDIDATS
# -----------------------------
categories = {
    "Meilleur joueur": [
        {"name": "Adel Boulbina (PAC)", "img": "boulbina.jpg"},
        {"name": "Aymen Mahious (CRB)", "img": "mahious.jpg"},
        {"name": "Abderrahmane Meziane (CRB)", "img": DEFAULT_IMG},
        {"name": "Ibrahim Dib (CSC)", "img": DEFAULT_IMG},
        {"name": "Salim Boukhenchouch (USMA)", "img": DEFAULT_IMG},
        {"name": "Larbi Tabti (MCA)", "img": DEFAULT_IMG},
        {"name": "Mehdi Boudjamaa (JSK)", "img": DEFAULT_IMG},
        {"name": "Hocine Metref (MCA)", "img": DEFAULT_IMG},
        {"name": "Rachid Nadji (CRB)", "img": DEFAULT_IMG},
        {"name": "Abdelkader Ghezzal (JSK)", "img": DEFAULT_IMG}
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

max_choices = {cat: 5 for cat in categories}
points = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# -----------------------------
# GOOGLE SHEETS
# -----------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")

# -----------------------------
# INFOS VOTANT
# -----------------------------
st.subheader("Informations du votant")
nom = st.text_input("📝 Nom et prénom")
tel = st.text_input("📞 Téléphone (9 chiffres)")

# -----------------------------
# FONCTION POUR VALIDER LE NUMERO
# -----------------------------
def valid_tel(t):
    return t.isdigit() and len(t) == 9

# -----------------------------
# VOTE PAR CATEGORIE
# -----------------------------
vote_data = {}

for cat, participants in categories.items():
    st.subheader(f"🏅 {cat}")
    remaining = participants.copy()
    selections = []

    for i in range(1, max_choices[cat]+1):
        st.markdown(f"**Choix #{i} :**")
        options = [p["name"] for p in remaining]
        default_index = 0  # ne pas pré-remplir
        selected_name = st.selectbox(
            "Sélectionner le candidat",
            options=[""] + options,  # vide par défaut
            index=default_index,
            key=f"{cat}_{i}"
        )

        if selected_name != "":
            # Afficher la photo à côté
            p_img = next((p["img"] for p in remaining if p["name"] == selected_name), DEFAULT_IMG)
            col1, col2 = st.columns([1,4])
            with col1:
                st.image(p_img, width=80)
            with col2:
                st.write(selected_name)
            selections.append(selected_name)
            # Retirer de la liste pour le prochain choix
            remaining = [p for p in remaining if p["name"] != selected_name]

    vote_data[cat] = selections

# -----------------------------
# ENREGISTRER LE VOTE
# -----------------------------
def save_vote(nom, tel, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        if "Téléphone" in df.columns and tel in df["Téléphone"].values:
            return False

    rows = []
    for cat, selections in votes.items():
        for i, candidat in enumerate(selections, start=1):
            rows.append([nom, tel, cat, candidat, points.get(i,0)])

    for r in rows:
        sheet.append_row(r)
    return True

# -----------------------------
# BOUTON ENVOI
# -----------------------------
if st.button("✅ Envoyer mon vote"):
    if not nom.strip():
        st.error("⚠️ Entrez votre nom")
    elif not valid_tel(tel.strip()):
        st.error("⚠️ Numéro invalide. Doit contenir 9 chiffres.")
    else:
        ok = save_vote(nom.strip(), tel.strip(), vote_data)
        if ok:
            st.success("✅ Vote enregistré !")
        else:
            st.error("⚠️ Ce numéro a déjà voté")

# -----------------------------
# RESULTATS
# -----------------------------
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
