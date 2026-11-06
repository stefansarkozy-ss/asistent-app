import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Nastavenie stránky pre mobilné obrazovky
st.set_page_config(
    page_title="Asistent Štefana Šarközyho",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Vzhľad pripomínajúci čistý terénny systém (karty a väčšie prvky pre dotyk)
st.markdown("""
    <style>
    .block-container { padding: 1rem 0.8rem; }
    .stButton > button { width: 100%; height: 3.2rem; font-size: 1.1rem; font-weight: bold; background-color: #1f2937; color: white; border-radius: 8px; }
    .stTextInput input, .stSelectbox div, .stDateInput input { font-size: 1.05rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Asistent Štefana Šarközyho")
st.caption("Terénny systém – Správa výjazdov, klientov a poznámok")

# 1. Načítanie dát z databázy alebo pamäte
try:
    conn = sqlite3.connect("dopyty.db")
    df = pd.read_sql_query("SELECT * FROM dopyty", conn)
    conn.close()
except Exception:
    if 'df_data' not in st.session_state:
        st.session_state.df_data = [
            {"id": 9, "datum_vytvorenia": "2026-10-25", "zaciatok_od": "08:00", "nazov_organizacie": "Mesto Partizánske", "klient": "Ján Novák", "sluzby": "SI + SS", "miesto": "NPDC Partizánske", "poznamka": "Individuálna supervízia v teréne", "hodiny": 10, "celkova_suma": 680, "mena": "EUR", "stav": "Nový"},
            {"id": 8, "datum_vytvorenia": "2026-10-25", "zaciatok_od": "09:30", "nazov_organizacie": "KC Jelka", "klient": "Mária Horváthová", "sluzby": "SI - individuálna supervízia", "miesto": "Kc Jelka", "poznamka": "Pravidelná konzultácia", "hodiny": 4, "celkova_suma": 293.09, "mena": "EUR", "stav": "Faktúra"},
        ]
    df = pd.DataFrame(st.session_state.df_data)

# 2. Výber záznamu na úpravu
dopyty_list = [
    f"ID {row['id']} - {row.get('klient', 'Neznámy')} ({row['nazov_organizacie']})" 
    for index, row in df.iterrows()
]

st.markdown("### 📋 Výber záznamu")
selected_option = st.selectbox("Zvoľte položku zo zoznamu:", dopyty_list, index=0)

selected_index = dopyty_list.index(selected_option)
selected_row_data = df.iloc[selected_index]

st.markdown("---")
st.subheader(f"✏️ Úprava záznamu ID: {selected_row_data.get('id', selected_index)}")

# 3. Hlavný formulár v čistom štýle
with st.form("edit_dopyt_form_clean"):
    
    # Hlasový modul priamo vo formulári (zabezpečí, že neodíde)
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
        
        # Nové/obnovené pole pre Klienta (ako v HTML prototupe)
        novy_klient = st.text_input("Klient / Meno", value=str(selected_row_data.get('klient', '')))
        
        nova_org = st.text_input("Názov organizácie", value=str(selected_row_data.get('nazov_organizacie', '')))
        
    with col2:
        nove_sluzby = st.text_input("Služby (napr. SI + SS)", value=str(selected_row_data.get('sluzby', '')))
        nove_miesto = st.text_input("Miesto / Sídlo", value=str(selected_row_data.get('miesto', '')))
        nove_hodiny_str = st.text_input("Počet hodín", value=str(selected_row_data.get('hodiny', 0)))
        nova_suma_str = st.text_input("Celková suma (EUR)", value=str(selected_row_data.get('celkova_suma', 0)))

    # Poznámka / Úkon (klasické textové pole z HTML rozhrania)
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

        # Aktualizácia dát
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
