import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

st.set_page_config(page_title="Inventaire PRO", layout="wide")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ---------------------------------------------------
# CONNECT GOOGLE SHEETS
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
        "inventaire": file.worksheet("Inventaire")
    }

sheets = connect_google()

# ---------------------------------------------------
# LOAD DATA SAFE
# ---------------------------------------------------

@st.cache_data(ttl=60)
def load_data():

    sku_df = pd.DataFrame(sheets["sku"].get_all_records())
    users_df = pd.DataFrame(sheets["users"].get_all_records())
    dist_df = pd.DataFrame(sheets["dist"].get_all_records())
    inv_df = pd.DataFrame(sheets["inventaire"].get_all_records())

    inv_df.columns = [str(c).strip() for c in inv_df.columns]

    required = [
        "DATE","ID_USER","USERS","ID_Dist","DISTRIBUTEUR",
        "MARQUE","CATEGORIE","ID_Produit","QTY","VALUE","STATUS"
    ]

    for c in required:
        if c not in inv_df.columns:
            inv_df[c] = ""

    return sku_df, users_df, dist_df, inv_df


sku_df, users_df, dist_df, inv_df = load_data()

# ---------------------------------------------------
# LOGIN SIMPLE
# ---------------------------------------------------

if "logged" not in st.session_state:
    st.session_state.logged = False

if "user" not in st.session_state:
    st.session_state.user = ""

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

    st.title("📦 INVENTAIRE PRO")

    st.write("User :", st.session_state.user)

    # ===================================================
    # FILTRE MARQUE → CATEGORIE → PRODUIT
    # ===================================================

    st.subheader("➕ Ajout produit")

    marque = st.selectbox("Marque", sku_df["MARQUE"].dropna().unique())

    cat_list = sku_df[sku_df["MARQUE"] == marque]["CATEGORIE"].dropna().unique()
    categorie = st.selectbox("Catégorie", cat_list)

    prod_list = sku_df[
        (sku_df["MARQUE"] == marque) &
        (sku_df["CATEGORIE"] == categorie)
    ]["ID"].dropna().unique()

    produit = st.selectbox("Produit", prod_list)

    qty = st.number_input("Quantité", min_value=0, step=1)

    dist = st.selectbox("Distributeur", dist_df["Distributeur"].dropna().unique())

    id_dist = dist_df[
        dist_df["Distributeur"] == dist
    ]["ID_Dist"].iloc[0]

    # ---------------------------------------------------
    # ADD ROW
    # ---------------------------------------------------

    if st.button("Ajouter"):

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.user,
            st.session_state.user,
            id_dist,
            dist,
            marque,
            categorie,
            produit,
            qty,
            qty * 0,   # VALUE placeholder
            "DRAFT"
        ]

        sheets["inventaire"].append_row(row)

        load_data.clear()
        st.success("Ajouté en DRAFT")
        st.rerun()

    # ===================================================
    # TABLE FILTERED DISPLAY
    # ===================================================

    st.subheader("📊 Inventaire")

    user_data = inv_df[
        inv_df["ID_USER"].astype(str) == str(st.session_state.user)
    ].copy()

    if user_data.empty:
        st.info("Aucune donnée")
        st.stop()

    # ---------------------------------------------------
    # AFFICHAGE LIMITÉ (IMPORTANT)
    # ---------------------------------------------------

    display_df = user_data[[
        "MARQUE",
        "CATEGORIE",
        "ID_Produit",
        "QTY",
        "STATUS"
    ]]

    st.dataframe(display_df, use_container_width=True)

    # ===================================================
    # FINALISATION SIMPLE
    # ===================================================

    st.subheader("🚀 Finalisation")

    if st.button("VALIDER DEFINITIVEMENT"):

        draft_rows = user_data[user_data["STATUS"] == "DRAFT"]

        for i, _ in draft_rows.iterrows():

            sheets["inventaire"].update(
                f"K{i+2}",
                [["FINAL"]]
            )

        load_data.clear()
        st.success("✔ Inventaire finalisé")
        st.rerun()
