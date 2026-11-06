import streamlit as st
import databaze
import validator
from moduly import dopyty_modul, fakturacia_modul, vyjazd_modul

# Inicializácia databázy a systémových tabuliek
databaze.init_db()
databaze.importuj_partnerov_z_csv()
validator.init_neuro_tables()

# Nastavenie stránky
st.set_page_config(
    page_title="Asistent Etien & Šarközy - Terénny Systém",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛡️ Asistent Štefana Šarközyho – Duálny Terénny Systém")
st.markdown("---")

# Hlavná navigácia / Výber modulu
menu = st.sidebar.selectbox(
    "Navigácia systému",
    ["Dopyty & Klienti", "Výjazdy & Cesty", "Fakturácia & iDoklad"]
)

if menu == "Dopyty & Klienti":
    dopyty_modul.render()
elif menu == "Výjazdy & Cesty":
    vyjazd_modul.render()
elif menu == "Fakturácia & iDoklad":
    fakturacia_modul.render()
