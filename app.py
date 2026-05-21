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

    inv_df = pd.DataFrame(sheets["inventaire"].get_all_records())

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

    # 🔥 MARQUE AJOUTÉE
    marque = st.selectbox(
        "Marque",
        sku_df["MARQUE"].dropna().unique()
    )

    # 🔥 CATEGORIE filtrée par MARQUE
    cat = st.selectbox(
        "Catégorie",
        sku_df[sku_df["MARQUE"] == marque]["CATEGORIE"].dropna().unique()
    )

    # PRODUITS filtrés par CATEGORIE
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
            str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            str(st.session_state.user),
            str(st.session_state.user),
            str(id_dist),
            str(dist),
            str(marque),     # ✅ MARQUE ajoutée ici
            str(cat),
            str(prod),
            float(qty),
            float(value),
            "DRAFT"
        ]

        sheets["inventaire"].append_row(row)

        load_data.clear()
        st.success("Ajouté en DRAFT")
        st.rerun()

    # ===================================================
    # TABLE
    # ===================================================

    st.subheader("📊 Inventaire")

    user_data = inv_df[
        inv_df["ID_USER"].astype(str) == str(st.session_state.user)
    ].copy()

    if user_data.empty:
        st.info("Aucune donnée")
        st.stop()

    draft_exists = (user_data["STATUS"] == "DRAFT").any()
    final_only = (user_data["STATUS"] == "FINAL").all()

    is_locked = final_only and not draft_exists

    if is_locked:

        st.dataframe(user_data, use_container_width=True)
        st.error("🔒 FINAL - verrouillé")

    else:

        edited = st.data_editor(user_data, use_container_width=True)

        if st.button("💾 Sauvegarder"):

            for i, row in edited.iterrows():

                try:
                    qty_val = float(row["QTY"])
                except:
                    qty_val = 0

                value = qty_val * 0

                sheets["inventaire"].update(
                    f"H{i+2}:J{i+2}",
                    [[qty_val, value, row["STATUS"]]]
                )

            load_data.clear()
            st.success("Sauvegardé")
            st.rerun()

        # ---------------------------------------------------
        # FINALISATION
        # ---------------------------------------------------

        st.subheader("🚀 ENVOI FINAL")
if False:
        if st.button("VALIDER DEFINITIVEMENT"):

            rows = user_data[user_data["STATUS"] == "DRAFT"]

            for i, _ in rows.iterrows():

                sheets["inventaire"].update(
                    f"J{i+2}",
                    [["FINAL"]]
                )

            load_data.clear()
            st.success("✔ FINAL OK")
            st.rerun()
