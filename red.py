import streamlit as st

# Vérifie si le bloc [google] est bien accessible
creds = st.secrets["google"]

print("✅ Secrets chargés avec succès !")
print("Project ID :", creds["project_id"])
print("Client email :", creds["client_email"])
