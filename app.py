import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Nastavenie stránky
st.set_page_config(
    page_title="Asistent Štefana Šarközyho",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Vizuálny dizajn - čisté karty, biely podklad a moderný vzhľad
st.markdown("""
    <style>
    .stApp {
        background-color: #f4f6f9;
    }
    .block-container { 
        padding: 1.5rem 1rem; 
        max-width: 700px;
    }
    /* Elegantné tmavé tlačidlo v štýle karty */
    .stButton > button { 
        width: 100%; 
        height: 3.2rem; 
        font-size: 1.1rem; 
        font-weight: 600; 
        background-color: #1f2937; 
        color: white; 
        border-radius: 10px; 
        border: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .stButton > button:hover {
        background-color: #374151;
        color: white;
    }
    /* Vstupné polia */
    .stTextInput input, .stSelectbox div, .stDateInput input, .stTextArea textarea { 
        font-size: 1.05rem; 
        border-radius: 8px !important;
        border: 1px solid #d1d5db !important;
    }
    /* Rámovanie formulára do čistej bielej karty */
    div.stForm {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e5e7eb;
    }
    </style>
""", unsafe_allow_html=True)

# Hlavička aplikácie
st.markdown("## 🛡️ Asistent Štefana Šarközyho")
st.caption("Terénny systém – Správa výjazdov, klientov a poznámok")
st.markdown("---")

# Načítanie dát
try:
    conn = sqlite3.connect("dopyty.db")
    df = pd.read_sql_query("SELECT * FROM dopyty", conn)
    conn.close()
except Exception:
    if 'df_data' not in st.session_state:
        st.session_state.df_data = [
            {"id": 9, "datum_vytvorenia": "2026-10-25", "zaciatok_od": "08:00", "nazov_organizacie": "Mesto Partizánske", "klient": "Ján Novák", "sluzby": "SI + SS", "miesto": "NPDC Partizánske", "poznamka": "Individuálna supervízia v teréne", "hodiny": 10, "celkova_suma": 680, "mena": "EUR", "stav": "Nový"},
        ]
    df = pd.DataFrame(st.session_state.df_data)

# Výber záznamu
dopyty_list = [
    f"ID {row['id']} - {row.get('klient', 'Neznámy')} ({row['nazov_organizacie']})" 
    for index, row in df.iterrows()
]

st.markdown("### 📋 Výber záznamu")
selected_option = st.selectbox("Zvoľte položku zo zoznamu:", dopyty_list, index=0)

selected_index = dopyty_list.index(selected_option)
selected_row_data = df.iloc[selected_index]

st.markdown("---")
st.markdown(f"### ✏️ Úprava záznamu ID: {selected_row_data.get('id', selected_index)}")

# Formulár v dizajne karty
with st.form("edit_dopyt_form_clean"):
    
    st.markdown("🎙️ **Hlasový vstup / Poznámka k výjazdu**")
    audio_file = st.audio_input("Nahrať hlasovú poznámku")
    if audio_file is not None:
        st.info("🎤 Hlasová nahrávka bola úspešne pripojená k záznamu.")

    col1, col2 = st.columns(2)
    
    with col1:
        povodny_datum_str = str(selected_row_data.get('datum_vytvorenia', datetime.now().strftime('%Y-%m-%d')))
        try:
            povodny_datum = datetime.strptime(povodny_datum_str.split()[0], '%Y-%m-%d').date()
        except Exception:
            povodny_datum = datetime.now().date()
            
        novy_datum = st.date_input("Dátum", value=povodny_datum)
        novy_zaciatok = st.text_input("Začiatok od", value=str(selected_row_data.get('zaciatok_od', '08:00')))
        novy_klient = st.text_input("Klient / Meno", value=str(selected_row_data.get('klient', '')))
        nova_org = st.text_input("Názov organizácie", value=str(selected_row_data.get('nazov_organizacie', '')))
        
    with col2:
        nove_sluzby = st.text_input("Služby (napr. SI + SS)", value=str(selected_row_data.get('sluzby', '')))
        nove_miesto = st.text_input("Miesto / Sídlo", value=str(selected_row_data.get('miesto', '')))
        nove_hodiny_str = st.text_input("Počet hodín", value=str(selected_row_data.get('hodiny', 0)))
        nova_suma_str = st.text_input("Celková suma (EUR)", value=str(selected_row_data.get('celkova_suma', 0)))

    nova_poznamka = st.text_area("Poznámka / Úkon", value=str(selected_row_data.get('poznamka', '')))

    povodny_stav = str(selected_row_data.get('stav', 'Nový'))
    stavy_zoznam = ["Nový", "Rozpracované", "Fakturácia", "Hotovo"]
    ind_stav = stavy_zoznam.index(povodny_stav) if povodny_stav in stavy_zoznam else 0
    novy_stav = st.selectbox("Stav záznamu", stavy_zoznam, index=ind_stav)

    submitted = st.form_submit_button("💾 Uložiť záznam")

    if submitted:
        try:
            finalne_hodiny = float(nove_hodiny_str.replace(',', '.'))
        except ValueError:
            finalne_hodiny = 0.0
            
        try:
            finalna_suma = float(nova_suma_str.replace(',', '.'))
        except ValueError:
            finalna_suma = 0.0

        df.at[selected_index, 'datum_vytvorenia'] = str(novy_datum)
        df.at[selected_index, 'zaciatok_od'] = novy_zaciatok
        df.at[selected_index, 'klient'] = novy_klient
        df.at[selected_index, 'nazov_organizacie'] = nova_org
        df.at[selected_index, 'sluzby'] = nove_sluzby
        df.at[selected_index, 'miesto'] = nove_miesto
        df.at[selected_index, 'poznamka'] = nova_poznamka
        df.at[selected_index, 'hodiny'] = finalne_hodiny
        df.at[selected_index, 'celkova_suma'] = finalna_suma
        df.at[selected_index, 'stav'] = novy_stav
        
        if 'df_data' in st.session_state:
            st.session_state.df_data = df.to_dict('records')
            
        st.success("Záznam bol úspešne uložený!")
        st.rerun()
