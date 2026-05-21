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
# GOOGLE SHEETS CONNECTION
# ---------------------------------------------------

@st.cache_resource
def connect_google():

    creds = Credentials.from_service_account_info(
        st.secrets["google"],
        scopes=SCOPES
    )

    client = gspread.authorize(creds)

    file = client.open_by_key(
        "10a1HUd0aGXJSWzVYjLtm3n5j9FjvvH5gz7Vot5wlLmc"
    )

    return {
        "sku": file.worksheet("SKU"),
        "users": file.worksheet("USERS"),
        "dist": file.worksheet("Distributeur"),
        "price": file.worksheet("Price"),
        "inventaire": file.worksheet("Inventaire")
    }

sheets = connect_google()

# ---------------------------------------------------
# CLEAN FUNCTION
# ---------------------------------------------------

def clean(v):
    if pd.isna(v):
        return ""
    return str(v)

# ---------------------------------------------------
# LOAD DATA SAFE (IMPORTANT FIX STATUS)
# ---------------------------------------------------

@st.cache_data(ttl=60)
def load_data():

    sku_df = pd.DataFrame(sheets["sku"].get_all_records())
    users_df = pd.DataFrame(sheets["users"].get_all_records())
    dist_df = pd.DataFrame(sheets["dist"].get_all_records())
    price_df = pd.DataFrame(sheets["price"].get_all_records())

    # ---------------- INVENTAIRE SAFE ----------------
    inv_raw = sheets["inventaire"].get_all_values()

    columns = [
        "DATE","ID_USER","USERS","ID_Dist",
        "DISTRIBUTEUR","CATEGORIE","ID_Produit",
        "QTY","VALUE","STATUS"
    ]

    if len(inv_raw) == 0 or len(inv_raw[0]) == 0:
        inv_df = pd.DataFrame(columns=columns)

    else:
        headers = [h.strip() for h in inv_raw[0]]
        rows = inv_raw[1:]

        inv_df = pd.DataFrame(rows, columns=headers)

    # clean columns
    inv_df.columns = inv_df.columns.str.strip()

    # 🔥 IMPORTANT FIX: STATUS ALWAYS EXISTS
    if "STATUS" not in inv_df.columns:
        inv_df["STATUS"] = "DRAFT"

    # ---------------- PRICE CLEAN ----------------
    if not price_df.empty:
        price_df["Prix_Distributeur"] = (
            price_df["Prix_Distributeur"]
            .astype(str)
            .str.replace(",", ".")
        )

        price_df["Prix_Distributeur"] = pd.to_numeric(
            price_df["Prix_Distributeur"],
            errors="coerce"
        ).fillna(0)

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

    user = st.text_input("Utilisateur")
    pwd = st.text_input("Mot de passe", type="password")

    if st.button("Connexion"):

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
    st.write("👤 Utilisateur :", st.session_state.user)

    # ---------------------------------------------------
    # USER DATA
    # ---------------------------------------------------

    user_data = inv_df[
        inv_df["ID_USER"].astype(str) == str(st.session_state.user)
    ].copy()

    if "STATUS" not in user_data.columns:
        user_data["STATUS"] = "DRAFT"

    # ---------------------------------------------------
    # ADD PRODUCT (DRAFT DIRECT)
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

    if st.button("Valider quantité"):

        prix_row = price_df[
            price_df["ID"].astype(str) == str(prod)
        ]

        prix = 0
        if not prix_row.empty:
            try:
                prix = float(prix_row.iloc[0]["Prix_Distributeur"])
            except:
                prix = 0

        value = int(qty) * prix

        sheets["inventaire"].append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.user,
            st.session_state.user,
            id_dist,
            dist,
            cat,
            prod,
            int(qty),
            value,
            "DRAFT"
        ])

        load_data.clear()

        st.success("Ajouté en DRAFT")
        st.rerun()

    # ---------------------------------------------------
    # EDITABLE TABLE (DRAFT ONLY)
    # ---------------------------------------------------

    st.subheader("📊 Historique modifiable")

    editable = user_data[user_data["STATUS"] == "DRAFT"].copy()

    if not editable.empty:

        editable = editable.reset_index()

        edited = st.data_editor(
            editable,
            use_container_width=True,
            num_rows="dynamic"
        )

        if st.button("💾 Sauvegarder modifications"):

            for _, row in edited.iterrows():

                sheet_row = row["index"] + 2

                sheets["inventaire"].update(
                    f"H{sheet_row}:I{sheet_row}",
                    [[row["QTY"], row["VALUE"]]]
                )

            load_data.clear()

            st.success("Modifications enregistrées")
            st.rerun()

    else:
        st.info("Aucun DRAFT")

    # ---------------------------------------------------
    # FINALISATION (FIX STATUS ERROR)
    # ---------------------------------------------------

    if st.button("🚀 ENVOI FINAL"):

        final_rows = user_data[user_data["STATUS"] == "DRAFT"].copy()
        final_rows = final_rows.reset_index()

        for _, row in final_rows.iterrows():

            sheet_row = row["index"] + 2

            sheets["inventaire"].update(
                f"J{sheet_row}",
                [["FINAL"]]
            )

        load_data.clear()

        st.success("Inventaire verrouillé")
        st.rerun()

    # ---------------------------------------------------
    # HISTORY
    # ---------------------------------------------------

    st.markdown("---")
    st.subheader("📋 Historique complet")

    st.dataframe(user_data, use_container_width=True)
