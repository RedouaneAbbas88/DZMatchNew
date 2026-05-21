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
# CLEAN PRICE SAFE
# ---------------------------------------------------

def get_price(prod_id, price_df):

    row = price_df[price_df["ID"].astype(str) == str(prod_id)]

    if row.empty:
        return 0

    try:
        val = row.iloc[0]["Prix_Distributeur"]
        return float(str(val).replace(",", "."))
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
# LOGIN
# ---------------------------------------------------

if "logged" not in st.session_state:
    st.session_state.logged = False

if "user" not in st.session_state:
    st.session_state.user = ""

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

    st.title("📦 Inventaire PRO")
    st.write("Utilisateur :", st.session_state.user)

    # ---------------------------------------------------
    # ADD PRODUCT
    # ---------------------------------------------------

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

        prix = get_price(prod, price_df)
        value = qty * prix

        sheets["inventaire"].append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.user,
            st.session_state.user,
            id_dist,
            dist,
            cat,
            prod,
            qty,
            value,
            "DRAFT"
        ])

        load_data.clear()
        st.success("Ajouté")
        st.rerun()

    # ---------------------------------------------------
    # LOAD USER DATA
    # ---------------------------------------------------

    user_data = inv_df[
        inv_df["ID_USER"].astype(str) == str(st.session_state.user)
    ].copy()

    # ---------------------------------------------------
    # STATUS CHECK
    # ---------------------------------------------------

    is_final = len(user_data[user_data["STATUS"] == "FINAL"]) > 0

    # ---------------------------------------------------
    # HISTORIQUE
    # ---------------------------------------------------

    st.subheader("📊 Historique")

    # 🔥 IMPORTANT: editable only if NOT FINAL
    if is_final:
        st.dataframe(user_data, use_container_width=True)
        st.error("🔒 Inventaire verrouillé (FINAL)")
    else:
        edited = st.data_editor(
            user_data,
            use_container_width=True,
            num_rows="dynamic"
        )

        if st.button("💾 Sauvegarder modifications"):

            for i, row in edited.iterrows():

                sheet_row = i + 2

                sheets["inventaire"].update(
                    f"H{sheet_row}:I{sheet_row}",
                    [[row["QTY"], row["VALUE"]]]
                )

            load_data.clear()
            st.success("Modifications enregistrées")
            st.rerun()

    # ---------------------------------------------------
    # FINAL BUTTON (AFTER TABLE)
    # ---------------------------------------------------

    if not is_final:

        st.subheader("🚀 Validation finale")

        if st.button("ENVOI FINAL"):

            draft_rows = user_data[user_data["STATUS"] == "DRAFT"]

            for i, row in draft_rows.iterrows():

                sheet_row = i + 2

                sheets["inventaire"].update(
                    f"J{sheet_row}",
                    [["FINAL"]]
                )

            load_data.clear()
            st.success("✔ Inventaire verrouillé")
            st.rerun()
