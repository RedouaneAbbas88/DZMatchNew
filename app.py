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
# LOAD DATA
# ---------------------------------------------------

@st.cache_data(ttl=60)
def load_data():

    sku_df = pd.DataFrame(sheets["sku"].get_all_records())
    users_df = pd.DataFrame(sheets["users"].get_all_records())
    dist_df = pd.DataFrame(sheets["dist"].get_all_records())
    price_df = pd.DataFrame(sheets["price"].get_all_records())
    inv_df = pd.DataFrame(sheets["inventaire"].get_all_records())

    return sku_df, users_df, dist_df, price_df, inv_df

sku_df, users_df, dist_df, price_df, inv_df = load_data()

# ---------------------------------------------------
# SESSION
# ---------------------------------------------------

if "logged" not in st.session_state:
    st.session_state.logged = False

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

if not st.session_state.logged:

    st.title("🔐 Connexion")

    user = st.text_input("Utilisateur")
    pwd = st.text_input("Mot de passe", type="password")

    if st.button("Connexion"):

        check = users_df[
            (users_df["ID_USER"] == user) &
            (users_df["PWD"] == pwd)
        ]

        if not check.empty:

            st.session_state.logged = True
            st.session_state.user = user

            st.success("Connexion réussie")
            st.rerun()

        else:
            st.error("Utilisateur ou mot de passe incorrect")

# ---------------------------------------------------
# MAIN APP
# ---------------------------------------------------

else:

    st.title("📦 Inventaire Distributeur")

    st.write(f"Connecté : {st.session_state.user}")

    # -------------------------------------------
    # DISTRIBUTEUR
    # -------------------------------------------

    dist_name = st.selectbox(
        "Sélectionner distributeur",
        dist_df["Distributeur"].unique()
    )

    dist_row = dist_df[
        dist_df["Distributeur"] == dist_name
    ].iloc[0]

    id_dist = dist_row["ID_Dist"]

    st.markdown("---")

    # -------------------------------------------
    # CATEGORIE
    # -------------------------------------------

    categorie = st.selectbox(
        "Catégorie",
        sku_df["CATEGORIE"].unique()
    )

    # -------------------------------------------
    # PRODUITS FILTRÉS
    # -------------------------------------------

    produits = sku_df[
        sku_df["CATEGORIE"] == categorie
    ]

    produit = st.selectbox(
        "Produit",
        produits["ID"].unique()
    )

    # -------------------------------------------
    # QUANTITE
    # -------------------------------------------

    qty = st.number_input(
        "Quantité",
        min_value=0,
        step=1
    )

    # -------------------------------------------
    # PRIX
    # -------------------------------------------

    prix_row = price_df[
        price_df["ID"] == produit
    ]

    prix = 0

    if not prix_row.empty:
        prix = float(prix_row.iloc[0]["Prix_Distributeur"])

    value = qty * prix

    # -------------------------------------------
    # SAVE
    # -------------------------------------------

    if st.button("✅ Valider"):

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # vérifier si déjà existe
        existing = inv_df[
            (inv_df["ID_USER"] == st.session_state.user) &
            (inv_df["ID_Dist"] == id_dist) &
            (inv_df["ID_Produit"] == produit)
        ]

        # UPDATE
        if not existing.empty:

            row_index = existing.index[0] + 2

            sheets["inventaire"].update(
                f"H{row_index}:I{row_index}",
                [[qty, value]]
            )

            st.success("Quantité modifiée")

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

            st.success("Inventaire enregistré")

        load_data.clear()
        st.rerun()

    st.markdown("---")

    # ---------------------------------------------------
    # HISTORIQUE
    # ---------------------------------------------------

    st.subheader("📋 Produits déjà saisis")

    historique = inv_df[
        (inv_df["ID_USER"] == st.session_state.user) &
        (inv_df["ID_Dist"] == id_dist)
    ]

    if not historique.empty:

        st.dataframe(
            historique[
                [
                    "CATEGORIE",
                    "ID_Produit",
                    "QTY"
                ]
            ],
            use_container_width=True
        )

    else:
        st.info("Aucune donnée")
