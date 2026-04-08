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
        {"name": "Adel Boulbina (PAC)", "img": "Assets/players/boulbina.jpg"},
        {"name": "Aymen Mahious (CRB)", "img": "Assets/players/mahious.jpg"},
        {"name": "Abderrahmane Meziane (CRB)", "img": "Assets/players/meziane.jpg"},
        {"name": "Ibrahim Dib (CSC)", "img": "Assets/players/dib.jpg"},
        {"name": "Salim Boukhenchouch (USMA)", "img": "Assets/players/boukhenchouch.jpg"},
        {"name": "Larbi Tabti (MCA)", "img": "Assets/players/tabti.jpg"},
        {"name": "Mehdi Boudjamaa (JSK)", "img": "Assets/players/boudjamaa.jpg"}
    ],
    "Meilleur gardien": [
        {"name": "Oussama Benbout (USMA)", "img": "Assets/players/benbout.jpg"},
        {"name": "Zakaria Bouhalfaya (CSC)", "img": "Assets/players/bouhalfaya.jpg"},
        {"name": "Abderrahmane Medjadel (ASO)", "img": "Assets/players/medjadel.jpg"},
        {"name": "Tarek Boussder (ESS)", "img": "Assets/players/boussder.jpg"},
        {"name": "Abdelkader Salhi (MCEB)", "img": "Assets/players/salhi.jpg"},
        {"name": "Moustapha Zeghba (CRB)", "img": "Assets/players/zeghba.jpg"}
    ],
    "Meilleur entraîneur": [
        {"name": "Khaled Benyahia (MCA)", "img": "Assets/players/benyahia.jpg"},
        {"name": "Joseph Zinbauer (JSK)", "img": "Assets/players/zinbauer.jpg"},
        {"name": "Sead Ramovic (CRB)", "img": "Assets/players/ramovic.jpg"},
        {"name": "Khereddine Madoui (CSC)", "img": "Assets/players/madoui.jpg"},
        {"name": "Bilal Dziri (PAC)", "img": "Assets/players/dziri.jpg"}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": "Assets/players/mca.jpg"},
        {"name": "USMA", "img": "Assets/players/usma.jpg"},
        {"name": "CSC", "img": "Assets/players/csc.jpg"},
        {"name": "CRB", "img": "Assets/players/crb.jpg"},
        {"name": "JSK", "img": "Assets/players/jsk.jpg"},
        {"name": "PAC", "img": "Assets/players/pac.jpg"},
        {"name": "ESS", "img": "Assets/players/ess.jpg"}
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
tel = st.text_input("📞 Téléphone")
media = st.text_input("📸 Média")

# ---------------------------------------------------
# FONCTION VOTE PAR CARTE
# ---------------------------------------------------
vote_data = {}

for cat, participants in categories.items():
    st.subheader(f"🏅 {cat}")
    remaining_players = participants.copy()
    selections = []

    for i in range(1, max_choices[cat]+1):
        st.markdown(f"**Choix #{i} :**")
        cols = st.columns(len(remaining_players))

        selected_player = None
        for idx, p in enumerate(remaining_players):
            with cols[idx]:
                st.image(p["img"], width=80)
                st.write(p["name"])
                if st.button(f"Choisir", key=f"{cat}_{i}_{p['name']}"):
                    selected_player = p["name"]

        if selected_player:
            selections.append(selected_player)
            # Retire le joueur sélectionné
            remaining_players = [p for p in remaining_players if p["name"] != selected_player]

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