import streamlit as st
import validator


def render():
  st.header("🚗 Terénny formulár výjazdu")
  st.caption("Manuálne zadanie alebo úprava prebiehajúceho výjazdu v teréne.")
  with st.form("manual_vyjazd"):
    text = st.text_area("Podrobný popis výjazdu, miesta a kazuistiky:")
    submitted = st.form_submit_button("Uložiť a spracovať výjazd")
    if submitted and text:
      res = validator.spracuj_vstup_koordinatorom(text)
      st.success(f"Výjazd úspešne uložený a vygenerovaný (ID: {res.get('id')})!")