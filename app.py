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
# IMAGES PAR DÉFAUT
# ---------------------------------------------------
DEFAULT_IMG = "Assets/defqult.jpg"  # image par défaut pour les candidats sans photo

# ---------------------------------------------------
# DONNÉES CATEGORIES AVEC PHOTOS LOCALES
# ---------------------------------------------------
categories = {
    "Meilleur joueur": [
        {"name": "Ferhat (mca)", "img": "boulbina.jpg"},
        {"name": "khacef (crb)", "img": "mahious.jpg"},
        {"name": "ghacha (usma)", "img": "defqult.jpg"},
        {"name": "belaid (jsk)", "img": "defqult.jpg"},
        {"name": "zerrouki (ess)", "img": "defqult.jpg"},
        {"name": "abada (aso/usma)", "img": "defqult.jpg"}
    ],
    "Meilleur gardien": [
        {"name": "salhi (jss)", "img": "defqult.jpg"},
        {"name": "benbout (usma)", "img": "defqult.jpg"},
        {"name": "guendouz (mca)", "img": "defqult.jpg"},
        {"name": "bouhalfaia (csc)", "img": "defqult.jpg"},
        {"name": "chaal (crb)", "img": "defqult.jpg"},
        {"name": "Ghaya merbah (jsk)", "img": "defqult.jpg"}
    ],
    "Meilleur entraîneur": [
        {"name": "Zegoud (Étoile de Ben Aknoun)", "img": "defqult.jpg"},
        {"name": "Lotfi Amrouche (Akbou / Sétif)", "img": "defqult.jpg"},
        {"name": "Ramović (CR Belouizdad)", "img": "defqult.jpg"},
        {"name": "Belaïd (Olympique Akbou)", "img": "defqult.jpg"},
        {"name": "Amrani (JS Saoura)", "img": "defqult.jpg"},
        {"name": "Chérif El Ouazzani (MC Oran)", "img": "defqult.jpg"}
    ],
    "Meilleur club": [
        {"name": "MCA", "img": "defqult.jpg"},
        {"name": "USMA", "img": "defqult.jpg"},
        {"name": "MCO", "img": "defqult.jpg"},
        {"name": "CRB", "img": "defqult.jpg"},
        {"name": "JSK", "img": "defqult.jpg"},
        {"name": "O. Akbou", "img": "defqult.jpg"},
        {"name": "ESBA", "img": "defqult.jpg"}
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
nom = st.text_input("📝 Nom et prénom", "")
tel = st.text_input("📞 Téléphone", "")
media = st.text_input("📸 Média", "")

# ---------------------------------------------------
# VALIDATION NUMÉRO TÉLÉPHONE
# ---------------------------------------------------
def is_valid_phone(t):
    return t.isdigit() and len(t) == 9

# ---------------------------------------------------
# VOTE PAR CLASSE AVEC AFFICHAGE PHOTO
# ---------------------------------------------------
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
            # Retirer le joueur choisi pour ne pas l'afficher dans la prochaine sélection
            remaining_players = [p for p in remaining_players if p["name"] != selected_name]

            # Affichage de la photo à côté
            p_img_name = next((p["img"] for p in participants if p["name"] == selected_name), "defqult.jpg")
            p_img_path = f"Assets/{p_img_name}"  # chemin exact
            col1, col2 = st.columns([1, 5])
            with col1:
                st.image(p_img_path, width=80)
            with col2:
                st.write(selected_name)

    vote_data[cat] = selections

# ---------------------------------------------------
# FONCTION POUR ENREGISTRER LE VOTE
# ---------------------------------------------------
def save_vote(nom, tel, media, votes):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Vérifier si le téléphone a déjà voté
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
# BOUTON ENVOI VOTE + PAGE DE CONFIRMATION AVEC EMOJI BALON + LOGO + RÉSULTATS
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
            # 🎉 Effet "ballons de foot" avec emojis
            st.markdown("⚽ ⚽ ⚽ ⚽ ⚽ ⚽ ⚽ ⚽ ⚽ ⚽", unsafe_allow_html=True)

            # Page de confirmation avec logo
            st.image("Assets/logo.PNG", width=200)
            st.markdown("**✅ Vote enregistré ! Merci pour votre participation !**")

            # Affichage immédiat des résultats
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
        else:
            st.error("⚠️ Vous avez déjà voté")
