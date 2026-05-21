import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Inventaire Distributeur",
    layout="wide"
)

# ---------------------------------------------------
# GOOGLE SHEETS CONNECTION
# ---------------------------------------------------

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

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
# LOAD DATA SAFE
# ---------------------------------------------------

@st.cache_data(ttl=60)
def load_data():

    sku_df = pd.DataFrame(sheets["sku"].get_all_records())
    users_df = pd.DataFrame(sheets["users"].get_all_records())
    dist_df = pd.DataFrame(sheets["dist"].get_all_records())
    price_df = pd.DataFrame(sheets["price"].get_all_records())

    # ---------------- INVENTAIRE SAFE ----------------
    inv_raw = sheets["inventaire"].get_all_values()

    expected_columns = [
        "DATE",
        "ID_USER",
        "USERS",
        "ID_Dist",
        "DISTRIBUTEUR",
        "CATEGORIE",
        "ID_Produit",
        "QTY",
        "VALUE"
    ]

    if len(inv_raw) == 0 or len(inv_raw[0]) == 0:
        inv_df = pd.DataFrame(columns=expected_columns)

    else:
        headers = inv_raw[0]
        rows = inv_raw[1:]

        if len(headers) != len(expected_columns):
            inv_df = pd.DataFrame(columns=expected_columns)
        else:
            inv_df = pd.DataFrame(rows, columns=headers)

    inv_df.columns = inv_df.columns.str.strip()

    # ---------------- CLEAN PRICE ----------------
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
# SESSION STATE
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
            st.error("Identifiants incorrects")

# ---------------------------------------------------
# MAIN APP
# ---------------------------------------------------

else:

    st.title("📦 Inventaire Distributeur")

    st.write("👤 Utilisateur :", st.session_state.user)

    # ---------------------------------------------------
    # DISTRIBUTEUR
    # ---------------------------------------------------

    dist_name = st.selectbox(
        "Distributeur",
        dist_df["Distributeur"].dropna().unique()
    )

    id_dist = dist_df[
        dist_df["Distributeur"] == dist_name
    ]["ID_Dist"].iloc[0]

    # ---------------------------------------------------
    # CATEGORIE
    # ---------------------------------------------------

    categorie = st.selectbox(
        "Catégorie",
        sku_df["CATEGORIE"].dropna().unique()
    )

    # ---------------------------------------------------
    # PRODUIT
    # ---------------------------------------------------

    produits = sku_df[
        sku_df["CATEGORIE"] == categorie
    ]["ID"].dropna().unique()

    produit = st.selectbox("Produit", produits)

    # ---------------------------------------------------
    # QUANTITE
    # ---------------------------------------------------

    qty = st.number_input("Quantité", min_value=0, step=1)

    # ---------------------------------------------------
    # PRIX
    # ---------------------------------------------------

    prix_row = price_df[
        price_df["ID"].astype(str) == str(produit)
    ]

    prix = 0

    if not prix_row.empty:
        try:
            prix = float(prix_row.iloc[0]["Prix_Distributeur"])
        except:
            prix = 0

    value = qty * prix

    st.info(f"💰 Valeur : {value:,.2f}")

    # ---------------------------------------------------
    # SAVE / UPDATE
    # ---------------------------------------------------

    if st.button("✅ Valider"):

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        existing = inv_df[
            (inv_df["ID_USER"].astype(str) == str(st.session_state.user)) &
            (inv_df["ID_Dist"].astype(str) == str(id_dist)) &
            (inv_df["ID_Produit"].astype(str) == str(produit))
        ]

        # UPDATE
        if not existing.empty:

            row_index = existing.index[0] + 2

            sheets["inventaire"].update(
                f"H{row_index}:I{row_index}",
                [[qty, value]]
            )

            st.success("Quantité mise à jour")

        # INSERT
        else:

            new_row = [
                now,
                st.session_state.user,
                st.session_state.user,
                id_dist,
                dist_name,
                categorie,
                produit,
                qty,
                value
            ]

            sheets["inventaire"].append_row(new_row)

            st.success("Produit ajouté")

        load_data.clear()
        st.rerun()

    # ---------------------------------------------------
    # HISTORIQUE
    # ---------------------------------------------------

    st.markdown("---")
    st.subheader("📋 Historique")

    historique = inv_df[
        (inv_df["ID_USER"].astype(str) == str(st.session_state.user)) &
        (inv_df["ID_Dist"].astype(str) == str(id_dist))
    ]

    if not historique.empty:

        st.dataframe(
            historique[
                ["CATEGORIE", "ID_Produit", "QTY", "VALUE"]
            ],
            use_container_width=True
        )

        total = historique["VALUE"].astype(float).sum()

        st.success(f"💰 Total inventaire : {total:,.2f}")

    else:
        st.info("Aucune donnée")

    # ---------------------------------------------------
    # REFRESH
    # ---------------------------------------------------

    if st.button("🔄 Actualiser"):
        load_data.clear()
        st.rerun()
