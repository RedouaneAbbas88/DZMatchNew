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
# CONNECT GOOGLE SHEETS
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
        "inventaire": file.worksheet("Inventaire"),
        "inventaire_final": file.worksheet("Inventaire_Final")
    }

sheets = connect_google()

# ---------------------------------------------------
# SAFE PRICE
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
    final_df = pd.DataFrame(sheets["inventaire_final"].get_all_records())

    return sku_df, users_df, dist_df, price_df, inv_df, final_df


sku_df, users_df, dist_df, price_df, inv_df, final_df = load_data()

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
    st.write("Utilisateur :", st.session_state.user)

    # ===================================================
    # 1. SAISIE INVENTAIRE (DRAFT)
    # ===================================================

    st.subheader("➕ Saisie inventaire")

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
        st.success("Ajouté en DRAFT")
        st.rerun()

    # ===================================================
    # 2. HISTORIQUE INVENTAIRE (EDITABLE)
    # ===================================================

    st.subheader("📊 Inventaire (modifiable)")

    user_data = inv_df[
        inv_df["ID_USER"].astype(str) == str(st.session_state.user)
    ]

    edited = st.data_editor(
        user_data,
        use_container_width=True
    )

    if st.button("💾 Sauvegarder modifications"):

        for i, row in edited.iterrows():

            sheets["inventaire"].update(
                f"H{i+2}:I{i+2}",
                [[row["QTY"], row["VALUE"]]]
            )

        load_data.clear()
        st.success("Modifications enregistrées")
        st.rerun()

    # ===================================================
    # 3. SAUVEGARDE VERS INVENTAIRE FINAL
    # ===================================================

    st.subheader("📦 Sauvegarder vers Inventaire Final")

    if st.button("SAUVEGARDER FINAL"):

        draft_rows = user_data[user_data["STATUS"] == "DRAFT"]

        rows_to_push = []

        for _, r in draft_rows.iterrows():

            rows_to_push.append([
                r["DATE"],
                r["ID_USER"],
                r["USERS"],
                r["ID_Dist"],
                r["DISTRIBUTEUR"],
                r["CATEGORIE"],
                r["ID_Produit"],
                r["QTY"],
                r["VALUE"],
                "READY"
            ])

        sheets["inventaire_final"].append_rows(rows_to_push)

        load_data.clear()
        st.success("Transféré vers Inventaire_Final")
        st.rerun()

    # ===================================================
    # 4. VALIDATION DEFINITIVE
    # ===================================================

    st.subheader("🚀 Validation définitive")

    final_user_data = final_df[
        final_df["ID_USER"].astype(str) == str(st.session_state.user)
    ]

    if not final_user_data.empty:

        if st.button("VALIDER DEFINITIVEMENT"):

            for i, _ in final_user_data.iterrows():

                sheets["inventaire_final"].update(
                    f"J{i+2}",
                    [["FINAL"]]
                )

            load_data.clear()
            st.success("✔ FINAL verrouillé")
            st.rerun()

    # ===================================================
    # 5. AFFICHAGE FINAL
    # ===================================================

    st.markdown("---")
    st.subheader("📋 Inventaire Final")

    st.dataframe(final_df, use_container_width=True)
