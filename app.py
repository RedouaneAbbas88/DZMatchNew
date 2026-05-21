import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

st.set_page_config(page_title="Inventaire SAFE PRO", layout="wide")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ---------------------------------------------------
# GOOGLE SHEETS
# ---------------------------------------------------

@st.cache_resource
def connect_google():

    creds = Credentials.from_service_account_info(
        st.secrets["google"],
        scopes=SCOPES
    )

    client = gspread.authorize(creds)
    file = client.open_by_key("10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc")

    return {
        "sku": file.worksheet("SKU"),
        "users": file.worksheet("USERS"),
        "dist": file.worksheet("Distributeur"),
        "price": file.worksheet("Price"),
        "inventaire": file.worksheet("Inventaire")
    }

sheets = connect_google()

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------

@st.cache_data(ttl=60)
def load_data():

    sku_df = pd.DataFrame(sheets["sku"].get_all_records())
    users_df = pd.DataFrame(sheets["users"].get_all_records())
    dist_df = pd.DataFrame(sheets["dist"].get_all_records())

    inv_df = pd.DataFrame(sheets["inventaire"].get_all_records())

    required_cols = [
        "DATE","ID_USER","USERS","ID_Dist","DISTRIBUTEUR",
        "MARQUE","CATEGORIE","ID_Produit","QTY","VALUE","STATUS"
    ]

    if inv_df.empty:
        inv_df = pd.DataFrame(columns=required_cols)

    for c in required_cols:
        if c not in inv_df.columns:
            inv_df[c] = ""

    return sku_df, users_df, dist_df, inv_df


sku_df, users_df, dist_df, inv_df = load_data()

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:

    st.title("🔐 LOGIN")

    user = st.text_input("User")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):

        check = users_df[
            (users_df["ID_USER"].astype(str) == str(user)) &
            (users_df["PWD"].astype(str) == str(pwd))
        ]

        if not check.empty:
            st.session_state.logged = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Login incorrect")

# ---------------------------------------------------
# APP
# ---------------------------------------------------

else:

    st.title("📦 INVENTAIRE")

    user_data = inv_df[
        inv_df["ID_USER"].astype(str) == str(st.session_state.user)
    ].copy()

    if user_data.empty:
        st.info("Aucune donnée")
        st.stop()

    # ---------------------------------------------------
    # 🔥 AFFICHAGE UNIQUEMENT COLONNES DEMANDÉES
    # ---------------------------------------------------

    cols = [
        "DATE",
        "DISTRIBUTEUR",
        "MARQUE",
        "CATEGORIE",
        "ID_Produit",
        "QTY"
    ]

    st.dataframe(user_data[cols], use_container_width=True)

    # ---------------------------------------------------
    # 🔥 EDITION SUR MÊME TABLE (SANS DUPLICATION)
    # ---------------------------------------------------

    edited = st.data_editor(user_data, use_container_width=True)

    # ---------------------------------------------------
    # SAVE
    # ---------------------------------------------------

    if st.button("💾 Sauvegarder"):

        for i, row in edited.iterrows():

            qty = float(row["QTY"]) if row["QTY"] != "" else 0
            value = qty * 0

            sheets["inventaire"].update(
                f"I{i+2}:K{i+2}",
                [[qty, value, row["STATUS"]]]
            )

        load_data.clear()
        st.success("Sauvegardé")
        st.rerun()
