import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

st.set_page_config(page_title="DZBEST 2025", layout="wide")
st.title("🏆 DZBEST 2025")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------- Fonctions -----------------
def get_img_path(filename):
    path = os.path.join(BASE_DIR, "Assets", filename)
    return path if os.path.exists(path) else os.path.join(BASE_DIR, "Assets", "default.jpg")

# ----------------- Données -----------------
players = [
    {"name": "Adel Boulbina (PAC)", "img": "boulbina.jpg"},
    {"name": "Aymen Mahious (CRB)", "img": "mahious.jpg"},
    {"name": "Abderrahmane Meziane (CRB)", "img": "default.jpg"},
    {"name": "Ibrahim Dib (CSC)", "img": "default.jpg"},
    {"name": "Salim Boukhenchouch (USMA)", "img": "default.jpg"},
    {"name": "Larbi Tabti (MCA)", "img": "default.jpg"},
    {"name": "Mehdi Boudjamaa (JSK)", "img": "default.jpg"}
]

MAX_TOP = 5

# ----------------- Infos votant -----------------
nom = st.text_input("📝 Nom et prénom")
tel = st.text_input("📞 Téléphone")
media = st.text_input("📸 Média")

# ----------------- Vote -----------------
selected_players = []
remaining_players = players.copy()

for rank in range(1, MAX_TOP+1):
    st.markdown(f"### Choix #{rank}")
    # Créer la liste déroulante avec noms
    options = [p["name"] for p in remaining_players]
    selected_name = st.selectbox("Sélectionnez un joueur :", options, key=f"top{rank}")
    
    # Trouver le joueur correspondant
    selected_player = next((p for p in remaining_players if p["name"] == selected_name), None)
    if selected_player:
        selected_players.append(selected_player)
        # Afficher sa photo à côté du nom
        st.image(get_img_path(selected_player["img"]), width=80)
        # Retirer de la liste pour les prochaines sélections
        remaining_players = [p for p in remaining_players if p["name"] != selected_name]

# ----------------- Afficher les choix finaux -----------------
st.markdown("## ✅ Vos sélections finales :")
for idx, p in enumerate(selected_players, start=1):
    st.markdown(f"**Classe {idx} : {p['name']}**")
    st.image(get_img_path(p["img"]), width=80)
