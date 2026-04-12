import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="DZBEST 2025", layout="wide")
st.title("🏆 DZBEST 2025")

# ---------------------------------------------------
# NAVIGATION
# ---------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "vote"

# ---------------------------------------------------
# DATA
# ---------------------------------------------------
categories = {
    "Meilleur joueur": [
        {"name": "Zineddine Ferhat (MCA)", "img": "ferhat.jpg"},
        {"name": "Mohamed Khacef(CRB)", "img": "khacef.jpg"},
        {"name": "Houssem Ghacha (USMA)", "img": "ghacha.jpg"},
        {"name": "Zineddine Belaid (JSK)", "img": "belaid.jpg"},
        {"name": "Merouane Zerrouki (ESS)", "img": "zerrouki.jpg"},
        {"name": "Achraf Abada (ASO/USMA)", "img": "abada.jpg"}
    ],
    "Meilleur gardien": [
        {"name": "Abdelkader Salhi (JSS)", "img": "salhi.jpg"},
        {"name": "Oussama Benbout (USMA)", "img": "benbout.jpg"},
        {"name": "Alexis Guendouz (MCA)", "img": "alexis.jpg"},
        {"name": "Farid Chaal (CRB)", "img": "chaal.jpg"},
        {"name": "Ghaya Merbah (JSK)", "img": "merbah.jpg"}
    ],
    "Meilleur entraîneur": [
        {"name": "Mounir Zegdoud (Étoile de Ben Aknoun)", "img": "mounir.jpg"},
        {"name": "Lotfi Amrouche (Akbou / Sétif)", "img": "amrouche.jpg"},
        {"name": "Sead Ramović (CRB)", "img": "sead.jpg"},
        {"name": "Abdelkader Amrani (JSS)", "img": "amrani.jpg"},
        {"name": "Chérif El Ouazzani (MCO)", "img": "cherif.jpg"}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": "MCA.jpg"},
        {"name": "USMA", "img": "USMA.jpg"},
        {"name": "MCO", "img": "MCO.jpg"},
        {"name": "CRB", "img": "CRB.jpg"},
        {"name": "JSK", "img": "JSK.jpg"},
        {"name": "O. AKBOU", "img": "akbou.jpg"},
        {"name": "ESBA", "img": "ESBA.jpg"}
    ]
}

max_choices = {cat: 5 for cat in categories}
points = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# ---------------------------------------------------
# GOOGLE SHEETS
# ---------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["google"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc").worksheet("Feuille 1")

# ---------------------------------------------------
# PAGE VOTE
# ---------------------------------------------------
if st.session_state.page == "vote":

    nom = st.text_input("📝 Nom et prénom")
    tel = st.text_input("📞 Téléphone")
    media = st.text_input("📸 Média")

    def is_valid_phone(t):
        return t.isdigit() and len(t) == 10

    vote_data = {}

    for cat, participants in categories.items():
        st.subheader(f"🏅 {cat}")
        remaining_players = participants.copy()
        selections = []

        for i in range(1, max_choices[cat]+1):
            st.markdown(f"**Choix #{i} :**")
            options = ["--- Sélectionnez ---"] + [p["name"] for p in remaining_players]
            selected_name = st.selectbox(f"Classe {i} - {cat}", options, key=f"{cat}_{i}")

            if selected_name != "--- Sélectionnez ---":
                selections.append(selected_name)
                remaining_players = [p for p in remaining_players if p["name"] != selected_name]

                p_img_name = next((p["img"] for p in participants if p["name"] == selected_name), "defqult.jpg")
                p_img_path = f"Assets/{p_img_name}"

                col1, col2 = st.columns([1, 5])
                with col1:
                    st.image(p_img_path, width=80)
                with col2:
                    st.write(selected_name)

        vote_data[cat] = selections

    def save_vote(nom, tel, media, votes):
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        if not df.empty and "Téléphone" in df.columns:
            if tel in df["Téléphone"].values:
                return False

        for cat, selections in votes.items():
            for i, candidat in enumerate(selections, start=1):
                sheet.append_row([nom, tel, media, cat, candidat, i, points.get(i, 0)])

        return True

    if st.button("✅ Envoyer mon vote"):

        if not nom.strip():
            st.error("⚠️ Entrez votre nom")
        elif not is_valid_phone(tel.strip()):
            st.error("⚠️ Numéro invalide")
        elif not media.strip():
            st.error("⚠️ Entrez votre média")
        else:
            ok = save_vote(nom.strip(), tel.strip(), media.strip(), vote_data)

            if ok:
                st.session_state.page = "results"
                st.rerun()
            else:
                st.error("⚠️ Vous avez déjà voté")

# ---------------------------------------------------
# PAGE RESULTATS
# ---------------------------------------------------
if st.session_state.page == "results":

    st.markdown("### ⚽ ⚽ ⚽ ⚽ ⚽ ⚽ ⚽")
    st.image("Assets/logo.PNG", width=200)
    st.success("✅ Vote enregistré !")

    data = sheet.get_all_records()

    if data:
        df = pd.DataFrame(data)
        df["Points"] = pd.to_numeric(df["Points"], errors="coerce")

        for cat, participants in categories.items():

            st.subheader(f"🏅 {cat}")

            df_cat = (
                df[df["Categorie"] == cat]
                .groupby("Candidat")["Points"]
                .sum()
                .reset_index()
                .sort_values(by="Points", ascending=False)
            )

            top5 = df_cat.head(5).copy()
            top5.insert(0, "Classement", range(1, len(top5)+1))

            # 🏆 PODIUM
            st.markdown("### 🥇 Podium")

            podium = top5.head(3)
            cols = st.columns(3)

            for i, (_, row) in enumerate(podium.iterrows()):
                name = row["Candidat"]
                pts = row["Points"]

                img = next((p["img"] for p in participants if p["name"] == name), "defqult.jpg")

                with cols[i]:
                    st.image(f"Assets/{img}", width=120)
                    st.markdown(f"**#{i+1} {name}**")
                    st.write(f"{pts} points")

            # 📊 TABLE
            st.markdown("### 📊 Classement")
            st.dataframe(top5, use_container_width=True, hide_index=True)