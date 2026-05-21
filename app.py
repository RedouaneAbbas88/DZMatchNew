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
# SAFE LOAD DATA
# ---------------------------------------------------

@st.cache_data(ttl=60)
def load_data():

    sku_df = pd.DataFrame(sheets["sku"].get_all_records())
    users_df = pd.DataFrame(sheets["users"].get_all_records())
    dist_df = pd.DataFrame(sheets["dist"].get_all_records())

    raw = sheets["inventaire"].get_all_records()
    inv_df = pd.DataFrame(raw)

    required_cols = [
        "DATE","ID_USER","USERS","ID_Dist","DISTRIBUTEUR",
        "MARQUE","CATEGORIE","ID_Produit","QTY","VALUE","STATUS"
    ]

    if inv_df.empty:
        inv_df = pd.DataFrame(columns=required_cols)

    inv_df.columns = [str(c).strip() for c in inv_df.columns]

    for c in required_cols:
        if c not in inv_df.columns:
            inv_df[c] = ""

    return sku_df, users_df, dist_df, inv_df


sku_df, users_df, dist_df, inv_df = load_data()

# ---------------------------------------------------
# SESSION
# ---------------------------------------------------

if "logged" not in st.session_state:
    st.session_state.logged = False

if "user" not in st.session_state:
    st.session_state.user = ""

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

if not st.session_state.logged:

    st.title("🔐 LOGIN SAFE")

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

    st.title("📦 INVENTAIRE SAFE PRO")
    st.write("Utilisateur :", st.session_state.user)

    # ===================================================
    # AJOUT PRODUIT
    # ===================================================

    st.subheader("➕ Ajouter produit")

    dist = st.selectbox("Distributeur", dist_df["Distributeur"].dropna().unique())

    id_dist = dist_df[
        dist_df["Distributeur"] == dist
    ]["ID_Dist"].iloc[0]

    marque = st.selectbox("Marque", sku_df["MARQUE"].dropna().unique())

    cat = st.selectbox(
        "Catégorie",
        sku_df[sku_df["MARQUE"] == marque]["CATEGORIE"].dropna().unique()
    )

    produits = sku_df[
        sku_df["CATEGORIE"] == cat
    ]["ID"].dropna().unique()

    prod = st.selectbox("Produit", produits)

    qty = st.number_input("Quantité", min_value=0, step=1)

    # ---------------------------------------------------
    # ADD ROW SAFE
    # ---------------------------------------------------

    if st.button("Ajouter"):

        value = qty * 0

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.user,
            st.session_state.user,
            id_dist,
            dist,
            marque,
            cat,
            prod,
            qty,
            value,
            "DRAFT"
        ]

        next_row = len(sheets["inventaire"].get_all_values()) + 1

        clean_row = [str(x) if x is not None else "" for x in row]

        sheets["inventaire"].update(
            f"A{next_row}:K{next_row}",
            [clean_row]
        )

        load_data.clear()
        st.success("Ajouté en DRAFT")
        st.rerun()

    # ===================================================
    # TABLE (MODIF ICI UNIQUEMENT)
    # ===================================================

    st.subheader("📊 Inventaire")

    user_data = inv_df[
        inv_df["ID_USER"].astype(str) == str(st.session_state.user)
    ].copy()

    if user_data.empty:
        st.info("Aucune donnée")
        st.stop()

    # 🔥 MODIF UNIQUEMENT ICI : colonnes affichées
    user_data = user_data[
        ["DATE", "DISTRIBUTEUR", "MARQUE", "CATEGORIE", "ID_Produit", "QTY", "STATUS"]
    ]

    edited = st.data_editor(user_data, use_container_width=True)

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
