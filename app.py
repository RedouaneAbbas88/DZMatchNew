```python
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
# STYLE
# ---------------------------------------------------

st.markdown("""
<style>

.main {
    padding-top: 20px;
}

.stButton button {
    width: 100%;
    height: 45px;
    font-size: 16px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

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

    sku_df = pd.DataFrame(
        sheets["sku"].get_all_records()
    )

    users_df = pd.DataFrame(
        sheets["users"].get_all_records()
    )

    dist_df = pd.DataFrame(
        sheets["dist"].get_all_records()
    )

    price_df = pd.DataFrame(
        sheets["price"].get_all_records()
    )

    inv_df = pd.DataFrame(
        sheets["inventaire"].get_all_records()
    )

    # -------------------------------------------
    # CLEAN PRICE
    # -------------------------------------------

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
# LOGIN PAGE
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

            st.success("Connexion réussie")

            st.rerun()

        else:

            st.error("Utilisateur ou mot de passe incorrect")

# ---------------------------------------------------
# MAIN APPLICATION
# ---------------------------------------------------

else:

    # ---------------------------------------------------
    # HEADER
    # ---------------------------------------------------

    col1, col2 = st.columns([8, 2])

    with col1:
        st.title("📦 Inventaire Distributeur")

    with col2:

        if st.button("Déconnexion"):

            st.session_state.logged = False
            st.session_state.user = ""

            st.rerun()

    st.write(f"👤 Connecté : {st.session_state.user}")

    st.markdown("---")

    # ---------------------------------------------------
    # DISTRIBUTEUR
    # ---------------------------------------------------

    distributeurs = dist_df["Distributeur"].dropna().unique()

    dist_name = st.selectbox(
        "Sélectionner un distributeur",
        distributeurs
    )

    dist_row = dist_df[
        dist_df["Distributeur"] == dist_name
    ].iloc[0]

    id_dist = dist_row["ID_Dist"]

    # ---------------------------------------------------
    # CATEGORIE
    # ---------------------------------------------------

    categories = sku_df["CATEGORIE"].dropna().unique()

    categorie = st.selectbox(
        "Catégorie",
        categories
    )

    # ---------------------------------------------------
    # PRODUITS
    # ---------------------------------------------------

    produits_df = sku_df[
        sku_df["CATEGORIE"] == categorie
    ]

    produits = produits_df["ID"].dropna().unique()

    produit = st.selectbox(
        "Produit",
        produits
    )

    # ---------------------------------------------------
    # QUANTITE
    # ---------------------------------------------------

    qty = st.number_input(
        "Quantité",
        min_value=0,
        step=1
    )

    # ---------------------------------------------------
    # PRIX
    # ---------------------------------------------------

    prix_row = price_df[
        price_df["ID"].astype(str) == str(produit)
    ]

    prix = 0

    if not prix_row.empty:

        prix_value = prix_row.iloc[0]["Prix_Distributeur"]

        try:
            prix = float(prix_value)

        except:
            prix = 0

    value = qty * prix

    # ---------------------------------------------------
    # INFO
    # ---------------------------------------------------

    st.info(f"💰 Valeur calculée : {value:,.2f} DZD")

    # ---------------------------------------------------
    # SAVE
    # ---------------------------------------------------

    if st.button("✅ Valider"):

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # -------------------------------------------
        # CHECK EXISTING PRODUCT
        # -------------------------------------------

        existing = inv_df[
            (inv_df["ID_USER"].astype(str) == str(st.session_state.user)) &
            (inv_df["ID_Dist"].astype(str) == str(id_dist)) &
            (inv_df["ID_Produit"].astype(str) == str(produit))
        ]

        # -------------------------------------------
        # UPDATE EXISTING
        # -------------------------------------------

        if not existing.empty:

            row_index = existing.index[0] + 2

            sheets["inventaire"].update(
                f"H{row_index}:I{row_index}",
                [[qty, value]]
            )

            st.success("✅ Quantité modifiée")

        # -------------------------------------------
        # INSERT NEW
        # -------------------------------------------

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

            st.success("✅ Produit ajouté")

        load_data.clear()

        st.rerun()

    # ---------------------------------------------------
    # HISTORIQUE
    # ---------------------------------------------------

    st.markdown("---")

    st.subheader("📋 Inventaire déjà saisi")

    historique = inv_df[
        (inv_df["ID_USER"].astype(str) == str(st.session_state.user)) &
        (inv_df["ID_Dist"].astype(str) == str(id_dist))
    ]

    if not historique.empty:

        historique = historique[
            [
                "CATEGORIE",
                "ID_Produit",
                "QTY"
            ]
        ]

        st.dataframe(
            historique,
            use_container_width=True
        )

        # -------------------------------------------
        # TOTAL VALUE
        # -------------------------------------------

        total_value = inv_df[
            (inv_df["ID_USER"].astype(str) == str(st.session_state.user)) &
            (inv_df["ID_Dist"].astype(str) == str(id_dist))
        ]["VALUE"].sum()

        st.success(
            f"💵 Valeur totale stock : {total_value:,.2f} DZD"
        )

    else:

        st.warning("Aucune donnée enregistrée")

    # ---------------------------------------------------
    # REFRESH BUTTON
    # ---------------------------------------------------

    if st.button("🔄 Actualiser"):

        load_data.clear()

        st.rerun()
```
