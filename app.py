import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Inventaire SAFE PRO",
    layout="wide"
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

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
# LOAD DATA
# ---------------------------------------------------

@st.cache_data(ttl=60)
def load_data():

    sku_df = pd.DataFrame(sheets["sku"].get_all_records())
    users_df = pd.DataFrame(sheets["users"].get_all_records())
    dist_df = pd.DataFrame(sheets["dist"].get_all_records())
    price_df = pd.DataFrame(sheets["price"].get_all_records())

    raw = sheets["inventaire"].get_all_records()
    inv_df = pd.DataFrame(raw)

    required_cols = [
        "DATE",
        "ID_USER",
        "USERS",
        "ID_Dist",
        "DISTRIBUTEUR",
        "MARQUE",
        "CATEGORIE",
        "ID_Produit",
        "QTY",
        "VALUE",
        "STATUS"
    ]

    if inv_df.empty:
        inv_df = pd.DataFrame(columns=required_cols)

    inv_df.columns = [str(c).strip() for c in inv_df.columns]

    for c in required_cols:
        if c not in inv_df.columns:
            inv_df[c] = ""

    return sku_df, users_df, dist_df, price_df, inv_df


sku_df, users_df, dist_df, price_df, inv_df = load_data()

# ---------------------------------------------------
# PRICE CLEANING (FIX IMPORTANT)
# ---------------------------------------------------

def clean_price(x):
    if pd.isna(x):
        return 0

    x = str(x)

    # enlever espaces normaux + insécables
    x = x.replace(" ", "").replace("\u202f", "")

    # remplacer virgule par point
    x = x.replace(",", ".")

    try:
        return float(x)
    except:
        return 0


price_dict = dict(
    zip(
        price_df["ID"].astype(str),
        price_df["Prix_Distributeur"].apply(clean_price)
    )
)

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

    dist_options = ["Tous"] + list(dist_df["Distributeur"].dropna().unique())

    dist = st.selectbox("Distributeur", dist_options)

    if dist != "Tous":
        id_dist = dist_df[
            dist_df["Distributeur"] == dist
        ]["ID_Dist"].iloc[0]
    else:
        id_dist = ""

    marque = st.selectbox(
        "Marque",
        sku_df["MARQUE"].dropna().unique()
    )

    cat = st.selectbox(
        "Catégorie",
        sku_df[sku_df["MARQUE"] == marque]["CATEGORIE"].dropna().unique()
    )

    produits = sku_df[
        sku_df["CATEGORIE"] == cat
    ]["ID"].dropna().unique()

    prod = st.selectbox("Produit", produits)

    qty = st.number_input("Quantité", min_value=0, step=1)

    # ===================================================
    # AJOUT
    # ===================================================

    if st.button("Ajouter"):

        if dist == "Tous":
            st.warning("Veuillez sélectionner un distributeur")

        else:

            try:
                price = float(price_dict.get(str(prod), 0))
                value = qty * price

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

                clean_row = [str(x) for x in row]

                sheets["inventaire"].append_row(clean_row)

                time.sleep(1)
                load_data.clear()

                st.success("Ajouté avec succès")
                st.rerun()

            except Exception as e:
                st.error(f"Erreur ajout : {e}")

    # ===================================================
    # TABLEAU
    # ===================================================

    st.subheader("📊 Inventaire")

    user_data = inv_df[
        inv_df["ID_USER"].astype(str) == str(st.session_state.user)
    ].copy()

    if dist != "Tous":
        user_data = user_data[
            user_data["DISTRIBUTEUR"].astype(str) == str(dist)
        ]

    if user_data.empty:
        st.info("Aucune donnée")
        st.stop()

    user_data = user_data.reset_index()

    display_data = user_data[
        [
            "index",
            "DATE",
            "DISTRIBUTEUR",
            "MARQUE",
            "CATEGORIE",
            "ID_Produit",
            "QTY",
            "STATUS"
        ]
    ]

    edited = st.data_editor(
        display_data,
        use_container_width=True,
        hide_index=True
    )

    # ===================================================
    # SAVE
    # ===================================================

    if st.button("💾 Sauvegarder"):

        try:
            for _, row in edited.iterrows():

                real_row = int(row["index"]) + 2

                qty = float(row["QTY"]) if str(row["QTY"]) != "" else 0
                prod_id = str(row["ID_Produit"])

                price = float(price_dict.get(prod_id, 0))
                value = qty * price

                sheets["inventaire"].update(
                    f"I{real_row}:K{real_row}",
                    [[qty, value, row["STATUS"]]]
                )

                time.sleep(1)

            load_data.clear()
            st.success("Sauvegarde effectuée")
            st.rerun()

        except Exception as e:
            st.error(f"Erreur sauvegarde : {e}")
