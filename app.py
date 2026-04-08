import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------
# ⚙️ Configuration Streamlit
# ---------------------------------------------------
st.set_page_config(
    page_title="DZBEST 2025",
    page_icon="Assets/logo.PNG",
    layout="wide"
)

# Header
col1, col2 = st.columns([1, 5])
with col1:
    st.image("Assets/logo.PNG", width=120)
with col2:
    st.title("🏆 DZBEST 2025")

# ---------------------------------------------------
# 🔹 Données avec images
# ---------------------------------------------------
categories = {
    "Meilleur joueur": [
        {
            "name": "Adel Boulbina (PAC)",
            "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"
        },
        {
            "name": "Aymen Mahious (CRB)",
            "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"
        }
    ],

    "Meilleur entraîneur": [
        {
            "name": "Khaled Benyahia (MCA)",
            "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"
        },
        {
            "name": "Joseph Zinbauer (JSK)",
            "img": "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"
        }
    ]
}

max_choices = {
    "Meilleur joueur": 2,
    "Meilleur entraîneur": 2
}

points = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}

# ---------------------------------------------------
# 🔹 Connexion Google Sheets
# ---------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = st.secrets["google"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

SPREADSHEET_ID = "10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc"
sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Feuille 1")

# ---------------------------------------------------
# 🔹 Infos votant
# ---------------------------------------------------
nom_votant = st.text_input("📝 Nom et prénom")
num_tel = st.text_input("📞 Téléphone")
media = st.text_input("📸 Média")

# ---------------------------------------------------
# 🔹 FORMULAIRE
# ---------------------------------------------------
vote_data = {}

with st.form("vote_form"):

    for cat, participants in categories.items():
        st.subheader(f"🏅 {cat}")

        selected = []
        cols = st.columns(4)

        for i, p in enumerate(participants):
            with cols[i % 4]:
                st.image(p["img"], use_container_width=True)
                if st.checkbox(p["name"], key=f"{cat}_{i}"):
                    selected.append(p["name"])

        vote_data[cat] = selected[:max_choices[cat]]

    submitted = st.form_submit_button("✅ Voter")

# ---------------------------------------------------
# 🔹 SAUVEGARDE
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
# 🔹 TRAITEMENT
# ---------------------------------------------------
if submitted:
    if not nom_votant or not num_tel or not media:
        st.error("⚠️ Remplir tous les champs")
    else:
        ok = save_vote(nom_votant, num_tel, media, vote_data)
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