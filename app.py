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
# GOOGLE SHEETS
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

    columns = [
        "DATE","ID_USER","USERS","ID_Dist",
        "DISTRIBUTEUR","CATEGORIE","ID_Produit","QTY","VALUE"
    ]

    if len(inv_raw) == 0 or len(inv_raw[0]) == 0:
        inv_df = pd.DataFrame(columns=columns)

    else:
        headers = inv_raw[0]

        if len(headers) != len(columns):
            inv_df = pd.DataFrame(columns=columns)
        else:
            inv_df = pd.DataFrame(inv_raw[1:], columns=headers)

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
# SESSION
# ---------------------------------------------------

if "logged" not in st.session_state:
    st.session_state.logged = False

if "user" not in st.session_state:
    st.session_state.user = ""

if "draft" not in st.session_state:
    st.session_state.draft = []

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

    st.title("📦 Inventaire Distributeur")

    st.write("👤 Utilisateur :", st.session_state.user)

    # ---------------- DISTRIBUTEUR ----------------

    dist_name = st.selectbox(
        "Distributeur",
        dist_df["Distributeur"].dropna().unique()
    )

    id_dist = dist_df[
        dist_df["Distributeur"] == dist_name
    ]["ID_Dist"].iloc[0]

    # ---------------- CATEGORIE ----------------

    categorie = st.selectbox(
        "Catégorie",
        sku_df["CATEGORIE"].dropna().unique()
    )

    # ---------------- PRODUIT ----------------

    produits = sku_df[
        sku_df["CATEGORIE"] == categorie
    ]["ID"].dropna().unique()

    produit = st.selectbox("Produit", produits)

    # ---------------- QUANTITE ----------------

    qty = st.number_input("Quantité", min_value=0, step=1)

    # ===================================================
    # AJOUT BROUILLON
    # ===================================================

    if st.button("➕ Ajouter au brouillon"):

        prix_row = price_df[
            price_df["ID"].astype(str) == str(produit)
        ]

        prix = 0
        if not prix_row.empty:
            try:
                prix = float(prix_row.iloc[0]["Prix_Distributeur"])
            except:
                prix = 0

        st.session_state.draft.append({
            "DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ID_USER": st.session_state.user,
            "USERS": st.session_state.user,
            "ID_Dist": id_dist,
            "DISTRIBUTEUR": dist_name,
            "CATEGORIE": categorie,
            "ID_Produit": produit,
            "QTY": int(qty),
            "VALUE": int(qty) * prix
        })

        st.success("Ajouté au brouillon")

    # ===================================================
    # TABLEAU BROUILLON (VALUE cachée)
    # ===================================================

    st.subheader("🧾 Brouillon")

    if st.session_state.draft:

        df_draft = pd.DataFrame(st.session_state.draft)

        display_df = df_draft.drop(columns=["VALUE"])

        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic"
        )

        # sync QTY seulement
        for i in range(len(edited_df)):
            st.session_state.draft[i]["QTY"] = edited_df.iloc[i]["QTY"]

    else:
        st.info("Aucun produit")

    # ===================================================
    # ENVOI FINAL
    # ===================================================

    if st.button("🚀 ENVOI FINAL"):

        if not st.session_state.draft:
            st.warning("Aucune donnée")
        else:

            rows = []

            for item in st.session_state.draft:

                prix_row = price_df[
                    price_df["ID"].astype(str) == str(item["ID_Produit"])
                ]

                prix = 0
                if not prix_row.empty:
                    try:
                        prix = float(prix_row.iloc[0]["Prix_Distributeur"])
                    except:
                        prix = 0

                value = int(item["QTY"]) * prix

                rows.append([
                    item["DATE"],
                    item["ID_USER"],
                    item["USERS"],
                    item["ID_Dist"],
                    item["DISTRIBUTEUR"],
                    item["CATEGORIE"],
                    item["ID_Produit"],
                    item["QTY"],
                    value
                ])

            sheets["inventaire"].append_rows(rows)

            st.session_state.draft = []

            load_data.clear()

            st.success("Inventaire envoyé avec succès")
            st.rerun()

    # ===================================================
    # HISTORIQUE
    # ===================================================

    st.markdown("---")
    st.subheader("📊 Historique")

    historique = inv_df[
        (inv_df["ID_USER"].astype(str) == str(st.session_state.user)) &
        (inv_df["ID_Dist"].astype(str) == str(id_dist))
    ]

    if not historique.empty:

        st.dataframe(
            historique[
                ["CATEGORIE","ID_Produit","QTY","VALUE"]
            ],
            use_container_width=True
        )

        total = historique["VALUE"].astype(float).sum()

        st.success(f"💰 Total : {total:,.2f}")

    else:
        st.info("Aucun inventaire")

    # ===================================================
    # RESET
    # ===================================================

    if st.button("🔄 Reset brouillon"):
        st.session_state.draft = []
        st.rerun()
