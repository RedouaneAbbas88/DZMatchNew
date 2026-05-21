import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

st.set_page_config(page_title="Inventaire PRO SIMPLE", layout="wide")

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
# PRICE SAFE
# ---------------------------------------------------

def get_price(prod_id, price_df):

    row = price_df[price_df["ID"].astype(str) == str(prod_id)]

    if row.empty:
        return 0

    try:
        return float(str(row.iloc[0]["Prix_Distributeur"]).replace(",", "."))
    except:
        return 0

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------

@st.cache_data(ttl=60)
def load_data():

    sku_df = pd.DataFrame(sheets["sku"].get_all_records())
    users_df = pd.DataFrame(sheets["users"].get_all_records())
    dist_df = pd.DataFrame(sheets["dist"].get_all_records())
    price_df = pd.DataFrame(sheets["price"].get_all_records())
    inv_df = pd.DataFrame(sheets["inventaire"].get_all_records())

    if "STATUS" not in inv_df.columns:
        inv_df["STATUS"] = "DRAFT"

    return sku_df, users_df, dist_df, price_df, inv_df


sku_df, users_df, dist_df, price_df, inv_df = load_data()

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

    st.title("🔐 Connexion")

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

    st.title("📦 Inventaire PRO SIMPLE")
    st.write("Utilisateur :", st.session_state.user)

    # ===================================================
    # 1. AJOUT
    # ===================================================

    st.subheader("➕ Ajouter produit")

    dist = st.selectbox("Distributeur", dist_df["Distributeur"].dropna().unique())

    id_dist = dist_df[
        dist_df["Distributeur"] == dist
    ]["ID_Dist"].iloc[0]

    cat = st.selectbox("Catégorie", sku_df["CATEGORIE"].dropna().unique())

    produits = sku_df[
        sku_df["CATEGORIE"] == cat
    ]["ID"].dropna().unique()

    prod = st.selectbox("Produit", produits)

    qty = st.number_input("Quantité", min_value=0, step=1)

    if st.button("Ajouter"):

        price = get_price(prod, price_df)
        value = qty * price

        sheets["inventaire"].append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.user,
            st.session_state.user,
            id_dist,
            dist,
            cat,
            prod,
            qty,
            price,
            value,
            "DRAFT"
        ])

        load_data.clear()
        st.success("Ajouté en DRAFT")
        st.rerun()

    # ===================================================
    # 2. TABLE
    # ===================================================

    st.subheader("📊 Inventaire")

    user_data = inv_df[
        inv_df["ID_USER"].astype(str) == str(st.session_state.user)
    ].copy()

    # ---------------------------------------------------
    # 🔥 CORRECTION LOGIQUE VERROUILLAGE
    # ---------------------------------------------------

    draft_exists = (user_data["STATUS"] == "DRAFT").any()
    final_only = (user_data["STATUS"] == "FINAL").all()

    is_locked = final_only and not draft_exists

    # ===================================================
    # 3. AFFICHAGE
    # ===================================================

    if is_locked:

        st.dataframe(user_data, use_container_width=True)
        st.error("🔒 Inventaire définitivement verrouillé")

    else:

        edited = st.data_editor(user_data, use_container_width=True)

        if st.button("💾 Sauvegarder modifications"):

            for i, row in edited.iterrows():

                price = float(row["PRICE"])
                qty = float(row["QTY"])
                value = price * qty

                sheets["inventaire"].update(
                    f"H{i+2}:J{i+2}",
                    [[qty, price, value]]
                )

            load_data.clear()
            st.success("Modifications enregistrées")
            st.rerun()

        # ===================================================
        # 4. FINALISATION
        # ===================================================

        st.subheader("🚀 Envoi final")

        if st.button("VALIDER DEFINITIVEMENT"):

            rows = user_data[user_data["STATUS"] == "DRAFT"]

            for i, _ in rows.iterrows():

                sheets["inventaire"].update(
                    f"K{i+2}",
                    [["FINAL"]]
                )

            load_data.clear()
            st.success("✔ Inventaire verrouillé")
            st.rerun()
