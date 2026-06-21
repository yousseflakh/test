import streamlit as st # type: ignore

# Configuration de la page
st.set_page_config(
    page_title="Application Streamlit",
    page_icon="🚀",
    layout="wide"
)

# Titre principal
st.title("Mon Application Streamlit")

# Sous-titre
st.subheader("Sous-titre de l'application")

# Texte
st.write("Ceci est un texte d'exemple pour l'application Streamlit.")

# Affichage de données
st.markdown("### Affichage de données")
data = {
    "Nom": ["Alice", "Bob", "Charlie"],
    "Âge": [25, 30, 35],
    "Ville": ["Paris", "Lyon", "Marseille"]
}
st.dataframe(data)

# Graphique simple
st.markdown("### Graphique")
import pandas as pd # type: ignore
import numpy as np

df = pd.DataFrame({
    "x": np.arange(10),
    "y": np.random.randn(10)
})
st.line_chart(df.set_index("x"))

# Widgets interactifs
st.markdown("### Widgets interactifs")
col1, col2 = st.columns(2)

with col1:
    nombre = st.slider("Choisissez un nombre", 0, 100, 50)
    st.write(f"Vous avez choisi : {nombre}")

with col2:
    option = st.selectbox("Choisissez une option", ["Option A", "Option B", "Option C"])
    st.write(f"Option sélectionnée : {option}")

# Bouton
if st.button("Cliquez ici"):
    st.success("Bouton cliqué !")

# Barre latérale
with st.sidebar:
    st.header("Menu latéral")
    st.radio("Sélectionnez une catégorie", ["Catégorie 1", "Catégorie 2", "Catégorie 3"])
    st.checkbox("Activer l'option")
    st.text_input("Entrez votre nom")

# Pied de page
st.markdown("---")
st.caption("© 2024 - Application Streamlit")