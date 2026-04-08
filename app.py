import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------
# ⚙️ Config
# ---------------------------------------------------
st.set_page_config(page_title="DZBEST 2025", layout="wide")

st.title("🏆 DZBEST 2025")

# ---------------------------------------------------
# 🔹 Données avec icônes
# ---------------------------------------------------
categories = {
    "Meilleur joueur": [
        "⚽ Adel Boulbina (PAC)",
        "⚽ Aymen Mahious (CRB)",
        "⚽ Abderrahmane Meziane (CRB)",
        "⚽ Ibrahim Dib (CSC)",
        "⚽ Salim Boukhenchouch (USMA)"
    ],
    "Meilleur gardien": [
        "🧤 Oussama Benbout (USMA)",
        "🧤 Zakaria Bouhalfaya (CSC)",
        "🧤 Moustapha Zeghba (CRB)"
    ],
    "Meilleur entraîneur": [
        "🎯 Khaled Benyahia (MCA)",
        "🎯 Joseph Zinbauer (JSK)",
        "🎯 Khereddine Madoui (CSC)"
    ],
    "Meilleur club": [
        "🏟️ MCA",
        "🏟️ USMA",
        "🏟️ CRB",
        "🏟️ JSK"
    ]
}

max_choices = {
    "Meilleur joueur": 5,
    "Meilleur gardien": 3,
    "Meilleur entraîneur": 3,
    "Meilleur club": 3
}

points = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# ---------------------------------------------------
# 🔹 Google Sheets
# ---------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google"], scopes=SCOPES
)
client = gspread.authorize(creds)

sheet = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")

# ---------------------------------------------------
# 🔹 Infos votant
# ---------------------------------------------------
nom = st.text_input("Nom et prénom")
tel = st.text_input("Téléphone")
media = st.text_input("Média")

# ---------------------------------------------------
# 🔹 FORMULAIRE
# ---------------------------------------------------
vote_data = {}

with st.form("vote_form"):

    for cat, participants in categories.items():
        st.subheader(f"🏅 {cat}")

        selections = []
        used = []

        for i in range(1, max_choices[cat] + 1):

            # filtrer pour éviter doublons
            options = [p for p in participants if p not in used]

            choice = st.selectbox(
                f"Choix #{i}",
                ["-- Choisir --"] + options,
                key=f"{cat}_{i}"
            )

            if choice != "-- Choisir --":
                selections.append(choice)
                used.append(choice)

        vote_data[cat] = selections

    submitted = st.form_submit_button("✅ Voter")

# ---------------------------------------------------
# 🔹 SAVE
# ---------------------------------------------------
def save_vote(nom, tel, media, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        if nom in df.get("Nom", [] ).values:
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

# ---------------------------------------------------
# 🔹 TRAITEMENT
# ---------------------------------------------------
if submitted:
    if not nom or not tel or not media:
        st.error("⚠️ Remplir tous les champs")
    else:
        ok = save_vote(nom, tel, media, vote_data)
        if ok:
            st.success("✅ Vote enregistré !")
        else:
            st.error("⚠️ Déjà voté")

# ---------------------------------------------------
# 🔹 RESULTATS
# ---------------------------------------------------
st.header("📊 Classement")

data = sheet.get_all_records()

if data:
    df = pd.DataFrame(data)
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")

    for cat in categories:
        st.subheader(cat)

        df_cat = (
            df[df["Categorie"] == cat]
            .groupby("Candidat")["Points"]
            .sum()
            .reset_index()
            .sort_values(by="Points", ascending=False)
        )

        df_cat.insert(0, "Classement", range(1, len(df_cat)+1))

        st.dataframe(df_cat, use_container_width=True, hide_index=True)