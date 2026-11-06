# ==========================================
# app.py - HLAVNÝ MASTER KOORDINÁTOR (STREAMLIT)
# ==========================================

import database
import streamlit as st
import validator
from modules import dopyty_modul, fakturacia_modul, vyjazd_modul

database.init_db()
database.importuj_partnerov_z_csv()
validator.init_neuro_tables()

st.set_page_config(
    page_title="Etien & Šarközy Asistent",
    layout="wide",
    page_icon="🧠",
)

st.sidebar.title("🌍 Etien & Šarközy System")
st.sidebar.caption("Dual-Entity Field Management (SR / ČR)")

aktivna_entita = st.sidebar.selectbox(
    "Aktívna dodávateľská entita:",
    [
        "Slovensko (SR) - PhDr. Štefan Šarközy",
        "Česká republika (ČR) - Etien Institut s.r.o.",
    ],
)

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navigácia",
    [
        "📥 Ambientná brána & Dopyty",
        "🚗 Terénny formulár",
        "🧾 Vnútorná fakturácia",
    ],
)

st.title("🧠 AI Terénny Koordinátor")

with st.expander(
    "🎙️ Rýchly hlasový / textový vstup (Ambient Intake Brána)", expanded=True
):
  col1, col2 = st.columns([3, 1])
  with col1:
    surovy_vstup = st.text_input(
        "Zadajte dopyt alebo nadiktujte poznámku (napr. 'Supervízia v"
        " Piešťanoch, 4 hodiny, riešili sme vyhorenie'):",
        key="ambient_input",
    )
  with col2:
    st.write("")
    st.write("")
    spracovat_btn = st.button(
        "Spracovať AI Koordinátorom", type="primary", use_container_width=True
    )

  if spracovat_btn and surovy_vstup:
    vysledok = validator.spracuj_vstup_koordinatorom(
        surovy_vstup, aktivna_entita
    )
    if vysledok["status"] == "Schválené":
      st.success(
          f"✅ Úspešne spracované a uložené! Partner:"
          f" **{vysledok['miesto']}** | Suma: **{vysledok['celkova_suma']}"
          f" {vysledok['mena']}**"
      )
      st.markdown(f"📅 [Uložiť do Google Kalendára]({vysledok['gcal_url']})")
    else:
      st.warning(f"⚠️ Guardrail aktivovaný: {vysledok['navrh_odpovedi']}")

st.markdown("---")

if menu == "📥 Ambientná brána & Dopyty":
  dopyty_modul.render()
elif menu == "🚗 Terénny formulár":
  vyjazd_modul.render()
elif menu == "🧾 Vnútorná fakturácia":
  fakturacia_modul.render()