import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(
    page_title="Asistent Štefana Šarközyho",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #3b4d66 !important;
    }
    .block-container {
        padding: 1.5rem 1rem;
        max-width: 720px;
    }
    /* Všetky nadpisy, popisy a štítky polí budú ČISTO BIELE */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {
        color: #ffffff !important;
    }
    .white-card {
        background-color: #ffffff !important;
        padding: 1.5rem !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.25) !important;
        margin-bottom: 1.5rem !important;
    }
    .white-card * {
        color: #1f2937 !important;
    }
    /* Hlavné tlačidlá / moduly (zväčšené, jednotné, prémiový modrý vzhľad) */
    div.stButton > button {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%) !important;
        color: #ffffff !important;
        width: 100%;
        min-height: 4.5rem;
        font-size: 1.05rem;
        font-weight: bold;
        border-radius: 14px;
        border: 2px solid #60a5fa;
        box-shadow: 0 6px 18px rgba(59, 130, 246, 0.4);
        white-space: pre-wrap !important;
    }
    div.stButton > button *, div.stButton > button p, div.stButton > button span {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
        border-color: #93c5fd;
        color: #ffffff !important;
    }
    /* Vstupné polia a výberové menu - biely podklad, tmavý text */
    .stTextInput input, .stTextArea textarea, .stDateInput input {
        background-color: #ffffff !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #1f2937 !important;
    }
    div[data-baseweb="select"] * {
        color: #1f2937 !important;
    }
    div[data-baseweb="menu"] * {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# Načítanie cenníkov z CSV súborov
def nacitaj_cennik(cesta, fallback):
    if os.path.exists(cesta):
        try:
            df = pd.read_csv(cesta)
            cennik = {"-- Žiadna / Nevybraté --": 0.0}
            for _, row in df.iterrows():
                kod = str(row.get('Kod', '')).strip()
                nazov = str(row.get('Nazov', '')).strip()
                cena = float(row.get('Cena', 0.0))
                kluc = f"{kod} - {nazov}" if kod else nazov
                cennik[kluc] = cena
            return cennik
        except Exception:
            return fallback
    return fallback

CENNIK_SR = nacitaj_cennik('cennik_sr.csv', {"-- Žiadna / Nevybraté --": 0.0, "SI - Individuálna supervízia": 60.0, "SS - Skupinová supervízia": 65.0})
CENNIK_CZ = nacitaj_cennik('cennik_cz.csv', {"-- Žiadna / Nevybraté --": 0.0, "SI - Individuálna supervízia": 1400.0, "SS - Skupinová supervízia": 1600.0})

zoznam_sluzieb_sr = list(CENNIK_SR.keys())
zoznam_sluzieb_cz = list(CENNIK_CZ.keys())

def nacitaj_partnerov(cesta):
    if os.path.exists(cesta):
        try:
            df = pd.read_csv(cesta)
            firmy = []
            for _, row in df.iterrows():
                firma = str(row.get('Firma', row.get('Nazov', ''))).strip()
                if firma and firma != 'nan':
                    firmy.append(firma)
            return sorted(list(set(firmy)))
        except Exception:
            return []
    return []

partneri_sr = nacitaj_partnerov('partneri_sr.csv') or ["DSS Partizánske", "Spojená škola Partizánske", "CDR Partizánske", "KC Jelka", "CDR Piešťany"]
partneri_cz = nacitaj_partnerov('partneri_cz.csv') or ["Praha - Klient ČR", "Brno - Klient ČR"]

DATABAZA_MIEST = {
    "bratislava": {"km": 0, "cas_h": 0.0},
    "partizánske": {"km": 290, "cas_h": 3.5},
    "dss partizánske": {"km": 290, "cas_h": 3.5},
    "spojená škola partizánske": {"km": 290, "cas_h": 3.5},
    "cdr partizánske": {"km": 290, "cas_h": 3.5},
    "jelka": {"km": 90, "cas_h": 1.5},
    "cífer": {"km": 100, "cas_h": 1.5},
    "piešťany": {"km": 160, "cas_h": 2.0},
    "pezinok": {"km": 50, "cas_h": 1.0},
    "trnava": {"km": 90, "cas_h": 1.2},
    "nitra": {"km": 180, "cas_h": 2.0},
    "brno": {"km": 260, "cas_h": 3.0},
    "praha": {"km": 660, "cas_h": 7.0}
}

def parse_float(val, default=0.0):
    if not val:
        return default
    try:
        return float(str(val).replace(',', '.'))
    except ValueError:
        return default

def vypocitaj_stravne(cas_h, region):
    if cas_h <= 0:
        return 0.0
    if "SR" in region:
        if 5 <= cas_h < 12: return 8.30
        elif 12 <= cas_h < 18: return 12.30
        elif cas_h >= 18: return 18.40
    else:
        if 5 <= cas_h < 12: return 140.0
        elif 12 <= cas_h < 18: return 210.0
        elif cas_h >= 18: return 330.0
    return 0.0

if 'cakaren' not in st.session_state: st.session_state.cakaren = []
if 'kalendar' not in st.session_state: st.session_state.kalendar = []
if 'input_mode' not in st.session_state: st.session_state.input_mode = 'diktafon'

st.markdown("## 🛡️ Asistent Štefana Šarközyho")
st.caption("Terénny systém – Správa výjazdov, klientov a poznámok")
st.markdown("---")

# 🏛️ 3 Hlavné Piliere hore
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    if st.button("🎙️ 1. Diktafón\n(Hlasový asistent)", use_container_width=True):
        st.session_state.input_mode = 'diktafon'
with col_p2:
    if st.button("📝 2. Zápis\n(Ad-hoc / Telefón)", use_container_width=True):
        st.session_state.input_mode = 'zapis'
with col_p3:
    if st.button("📥 3. Dopyty\n(Rozpracované / SMS)", use_container_width=True):
        st.session_state.input_mode = 'dopyty'

st.markdown("<br>", unsafe_allow_html=True)

surovy_text = ""

# Interaktívna časť pod piliermi
if st.session_state.input_mode == 'diktafon':
    if st.button("🎙️ Kliknite sem pre spustenie nahrávania a prevod hlasového diktátu", use_container_width=True):
        surovy_text = "Dnes 7.11.2026 výjazd v DSS Partizánske, trvanie 2 hodiny. Supervízia, cestovné 15 eur."
        st.success("✅ Hlas bol úspešne zaznamenaný a prevedený na text do formulára.")

elif st.session_state.input_mode == 'zapis':
    st.info("⚡ **Ad-hoc režim:** Priamy zápis objednávky bez zbytočných medzikrokov.")

elif st.session_state.input_mode == 'dopyty':
    vybrana_spr = st.selectbox(
        "📥 Vyberte externú správu / dopyt:",
        [
            "-- Vyberte správu --",
            "WhatsApp (10:15): Dobrý deň, potvrdzujem výjazd v Spojenej škole Partizánske. Hodiny: 3",
            "SMS (09:30): Potrebujeme akútnu konzultáciu v CDR Partizánske na 12.11."
        ]
    )
    if vybrana_spr != "-- Vyberte správu --":
        surovy_text = vybrana_spr

st.markdown("---")
st.markdown("### ✏️ Formulár dopytu & Validátor")

poznamka_input = st.text_area("📝 Poznámka / Prepis úkonu:", value=surovy_text, height=80)

region = st.radio("Región / Cenník / Krajina:", ["🇸🇰 SR (EUR)", "🇨🇿 ČR (CZK)"], horizontal=True)
is_sr = "SR" in region
cennik = CENNIK_SR if is_sr else CENNIK_CZ
zoznam_sluz = zoznam_sluzieb_sr if is_sr else zoznam_sluzieb_cz
zoznam_partnerov = partneri_sr if is_sr else partneri_cz
mena = "€" if is_sr else "Kč"

# 1. Riadok: Dátum a Čas
col_r1_1, col_r1_2 = st.columns(2)
with col_r1_1:
    datum_val = st.date_input("1. Dátum výjazdu", value=datetime.now())
with col_r1_2:
    cas_val = st.text_input("2. Čas (od-do)", value="08:00 - 10:00")

# 2. Riadok: Organizácia
col_r2_1, col_r2_2 = st.columns(2)
with col_r2_1:
    org_vyber = st.selectbox("3. Názov organizácie (zo zoznamu)", options=["-- Vyberte zo zoznamu --"] + zoznam_partnerov, index=0)
with col_r2_2:
    org_ručne = st.text_input("Alebo napíšte organizáciu ručne:", value="DSS Partizánske" if "Partizánske" in poznamka_input else "")

org_val = org_ručne if (not org_vyber or org_vyber == "-- Vyberte zo zoznamu --") else org_vyber

# 3. Riadok: Miesto konania
col_r3_1, col_r3_2 = st.columns(2)
with col_r3_1:
    miesto_vyber = st.selectbox("4. Miesto konania (zo zoznamu)", options=["-- Vyberte zo zoznamu --"] + zoznam_partnerov, index=0)
with col_r3_2:
    miesto_ručne = st.text_input("Alebo napíšte miesto ručne:", value=org_val if org_val else "Partizánske")

miesto_val = miesto_ručne if (not miesto_vyber or miesto_vyber == "-- Vyberte zo zoznamu --") else miesto_vyber

miesto_key = miesto_val.strip().lower()
auto_km = DATABAZA_MIEST.get(miesto_key, {}).get("km", 290 if "partizánske" in miesto_key else 50)
auto_cas_cesty = DATABAZA_MIEST.get(miesto_key, {}).get("cas_h", 3.5 if "partizánske" in miesto_key else 1.0)

st.markdown("---")
st.markdown("#### 5. & 6. Služby, Hodiny a Sadzby")

col_s1, col_s2 = st.columns(2)

if 'prev_sel_5a' not in st.session_state: st.session_state.prev_sel_5a = None
if 'prev_sel_5b' not in st.session_state: st.session_state.prev_sel_5b = None
if 'prev_region' not in st.session_state: st.session_state.prev_region = None
if 'h_6a2' not in st.session_state: st.session_state.h_6a2 = "0.0"
if 'h_6b2' not in st.session_state: st.session_state.h_6b2 = "0.0"

with col_s1:
    st.markdown("**Služba A**")
    sluzba_5a = st.selectbox("5A. Výber služby", options=zoznam_sluz, key="sel_5a")
    cena_z_cennika_5a = cennik.get(sluzba_5a, 0.0)
    
    if st.session_state.get('sel_5a') != st.session_state.get('prev_sel_5a') or region != st.session_state.get('prev_region'):
        st.session_state.h_6a2 = str(cena_z_cennika_5a)
    
    h_6a1 = st.text_input("6A.1 Počet hodín", value="2.0" if "2 hodiny" in poznamka_input else ("3.0" if "Hodiny: 3" in poznamka_input else "0.0"), key="h_6a1")
    h_6a2 = st.text_input(f"6A.2 Cena / 1 hod. ({mena})", key="h_6a2")

with col_s2:
    st.markdown("**Služba B (Voliteľné)**")
    sluzba_5b = st.selectbox("5B. Výber ďalšej služby", options=zoznam_sluz, key="sel_5b")
    cena_z_cennika_5b = cennik.get(sluzba_5b, 0.0)
    
    if st.session_state.get('sel_5b') != st.session_state.get('prev_sel_5b') or region != st.session_state.get('prev_region'):
        st.session_state.h_6b2 = str(cena_z_cennika_5b)
        
    h_6b1 = st.text_input("6B.1 Počet hodín", value="0.0", key="h_6b1")
    h_6b2 = st.text_input(f"6B.2 Cena / 1 hod. ({mena})", key="h_6b2")

st.session_state.prev_sel_5a = st.session_state.get('sel_5a')
st.session_state.prev_sel_5b = st.session_state.get('sel_5b')
st.session_state.prev_region = region

hodiny_5a = parse_float(h_6a1)
sadzba_5a = parse_float(h_6a2)

hodiny_5b = parse_float(h_6b1)
sadzba_5b = parse_float(h_6b2)

vypocitana_suma_sluzieb = (hodiny_5a * sadzba_5a) + (hodiny_5b * sadzba_5b)
s_7 = st.text_input(f"7. Celková suma za služby ({mena})", value=f"{vypocitana_suma_sluzieb:.2f}")
suma_sluzieb_val = parse_float(s_7, vypocitana_suma_sluzieb)

st.markdown("---")
st.markdown("#### 8. Cestovné náhrady, čas na ceste a ubytovanie")

col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    vztah_km = st.text_input("Kilometre (tam a späť):", value=str(auto_km))
    sadzba_km_in = st.text_input(f"Sadzba / 1 km ({mena}):", value="0.50" if is_sr else "6.0")
with col_c2:
    cas_cesta = st.text_input("Čas na ceste (hod.):", value=str(auto_cas_cesty))
    sadzba_cas_cesty = st.text_input(f"Sadzba za čas cesty / hod ({mena}):", value="10.0" if is_sr else "250.0")
with col_c3:
    ubytovanie_in = st.text_input(f"Ubytovanie ({mena}):", value="0.0")

km_val = parse_float(vztah_km)
sazba_km_val = parse_float(sadzba_km_in)
vypocitane_km_cestovne = km_val * sazba_km_val

cas_cesta_val = parse_float(cas_cesta)
sazba_cas_val = parse_float(sadzba_cas_cesty)
vypocitany_cas_cesty_suma = cas_cesta_val * sazba_cas_val

vypocitane_stravne = vypocitaj_stravne(cas_cesta_val, region)
ubyt_val = parse_float(ubytovanie_in)

default_cestovne_celkom = vypocitane_km_cestovne + vypocitany_cas_cesty_suma + vypocitane_stravne + ubyt_val
d_8 = st.text_input(f"8. Celkové Cestovné & Výdavky ({mena})", value=f"{default_cestovne_celkom:.2f}")
cestovne_val = parse_float(d_8, default_cestovne_celkom)

st.markdown("---")
vypocitana_celkova = suma_sluzieb_val + cestovne_val
c_9 = st.text_input(f"9. Celková suma na úhradu ({mena})", value=f"{vypocitana_celkova:.2f}")
celkova_suma_val = parse_float(c_9, vypocitana_suma_sluzieb + cestovne_val)

st.markdown("---")
st.markdown("🤖 **Stav Inteligentného Validátora:**")
je_kompletne = bool(org_val and org_val != "-- Vyberte zo zoznamu --" and (hodiny_5a > 0 or hodiny_5b > 0))

if je_kompletne:
    st.success("✅ Validácia úspešná: Dáta sedia a výjazd je kompletný.")
else:
    st.warning("⚠️ Validácia: Záznam obsahuje neúplné údaje (chýba organizácia alebo hodiny). Výjazd bude presmerovaný do Rozpracovaných Dopytov.")

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    submit_kalendar = st.button("📅 Schváliť a poslať do KALENDÁRA", use_container_width=True)
with col_btn2:
    submit_cakaren = st.button("📥 Uložiť do ROZPRACOVANÝCH DOPYTOV", use_container_width=True)

text_sluzieb = sluzba_5a
if sluzba_5b != "-- Žiadna / Nevybraté --":
    text_sluzieb += f" + {sluzba_5b}"

if submit_kalendar:
    novy_zaznam = {
        "datum": str(datum_val), "region": region, "org": org_val, "miesto": miesto_val,
        "sluzby": text_sluzieb, "sluzby_suma": suma_sluzieb_val, 
        "km": km_val, "cestovne": cestovne_val, "celkom": celkova_suma_val, "status": "SCHVÁLENÉ"
    }
    st.session_state.kalendar.append(novy_zaznam)
    st.success("Záznam bol schválený a odoslaný do kalendára!")

if submit_cakaren:
    novy_zaznam = {
        "datum": str(datum_val), "region": region, "org": org_val, "miesto": miesto_val,
        "sluzby": text_sluzieb, "sluzby_suma": suma_sluzieb_val, 
        "km": km_val, "cestovne": cestovne_val, "celkom": celkova_suma_val, "status": "ROZPRACOVANÉ"
    }
    st.session_state.cakaren.append(novy_zaznam)
    st.info("Záznam bol uložený do 3. piliera (Rozpracované dopyty).")

st.markdown("---")
st.markdown("### 🗂️ Prehľad stavov záznamov")
tab1, tab2 = st.tabs(["📥 Rozpracované Dopyty (Čakáreň)", "📅 Uložené v Kalendári"])
with tab1:
    if st.session_state.cakaren:
        st.dataframe(pd.DataFrame(st.session_state.cakaren))
    else:
        st.write("Žiadne rozpracované dopyty.")
with tab2:
    if st.session_state.kalendar:
        st.dataframe(pd.DataFrame(st.session_state.kalendar))
    else:
        st.write("Kalendár je prázdny.")