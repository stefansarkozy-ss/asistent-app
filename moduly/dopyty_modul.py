# ==========================================
# modules/dopyty_modul.py - SPRÁVA DOPYTOV
# ==========================================

import pandas as pd
import streamlit as st
from databaze import get_connection


def render():
    st.header("📥 Správa dopytov a čakajúcich úloh")
    st.caption(
        "Prehľad všetkých zaevidovaných dopytov, výjazdov a stavov spracovania."
    )

    conn = get_connection()
    df = pd.read_sql("SELECT * FROM dopyty ORDER BY id DESC", conn)
    conn.close()

    if df.empty:
        st.info("Zatiaľ nie sú zaevidované žiadne dopyty.")
    else:
        st.dataframe(
            df[[
                "id",
                "datum_vytvorenia",
                "sluzby",
                "miesto",
                "krajina",
                "hodiny",
                "celkova_suma",
                "mena",
                "stav",
            ]],
            use_container_width=True,
        )