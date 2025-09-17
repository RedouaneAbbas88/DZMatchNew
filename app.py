import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="DZMatch Votes", layout="wide")
st.title("🏆 DZMatch Votes")

# -------------------------------
# 🔹 Définir les catégories et participants
# -------------------------------
categories = {
    "Meilleur gardien": ["Oussama", "Zakaria", "Abderrahmane", "Tarek"],
    "Meilleur club": ["MCA", "USMA", "CSC", "CRB"],
    "Meilleur joueur": ["Adel", "Aymen", "Ibrahim", "Salim"],
    "Meilleur entraîneur": ["Khaled", "Joseph", "Sead", "Bilal"]
}

# -------------------------------
# 🔹 Barème des points
# -------------------------------
points = {1:5, 2:3, 3:2, 4:1, 5:0.5}

# -------------------------------
# 🔹 Nom du votant
# -------------------------------
nom_votant = st.text_input("📝 Entrez votre nom et prénom :")

# -------------------------------
# 🔹 Formulaire de vote
# -------------------------------
vote_data = {}
with st.form("vote_form"):
    for cat, participants in categories.items():
        st.subheader(cat)
        top5 = st.multiselect(
            f"Sélectionnez votre TOP 5 pour {cat} (ordre important)",
            options=participants,
            max_selections=5,
            key=cat
        )
        vote_data[cat] = top5

    submitted = st.form_submit_button("✅ Envoyer mon vote")

# -------------------------------
# 🔹 Fichier Excel
# -------------------------------
excel_file = Path("votes.xlsx")

# -------------------------------
# 🔹 Fonction pour sauvegarder le vote
# -------------------------------
def save_vote(nom, votes):
    if excel_file.exists():
        df = pd.read_excel(excel_file)
    else:
        df = pd.DataFrame(columns=["Nom","Categorie","Candidat","Position","Points"])

    # Vérifier si le votant a déjà voté
    if nom in df["Nom"].values:
        return False

    # Ajouter les votes
    for cat, top5 in votes.items():
        for i, candidat in enumerate(top5, start=1):
            df = pd.concat([df, pd.DataFrame([[nom, cat, candidat, i, points.get(i,0)]],
                        columns=df.columns)], ignore_index=True)

    df.to_excel(excel_file, index=False)
    return True

# -------------------------------
# 🔹 Traitement du vote
# -------------------------------
if submitted:
    if not nom_votant.strip():
        st.error("⚠️ Vous devez entrer votre nom et prénom avant de voter.")
    else:
        success = save_vote(nom_votant, vote_data)
        if success:
            st.success(f"Merci {nom_votant}, votre vote a été enregistré ! 🎉")
        else:
            st.error("⚠️ Vous avez déjà voté.")

# -------------------------------
# 🔹 Affichage des résultats
# -------------------------------
st.header("📊 Classements en temps réel")
if excel_file.exists():
    df = pd.read_excel(excel_file)
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")

    for cat in categories:
        st.subheader(cat)
        df_cat = df[df["Categorie"]==cat].groupby("Candidat")["Points"].sum().reset_index()
        df_cat = df_cat.sort_values(by="Points", ascending=False)
        df_cat.insert(0,"Position", range(1, len(df_cat)+1))
        st.dataframe(df_cat, use_container_width=True)
