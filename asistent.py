# ==========================================
# ASISTENT ŠTEFANA ŠARKÖZYHA - DUÁLNY TERÉNNY SYSTÉM S AI KOORDINÁTOROM
# (MOBILE-TOUCH OPTIMIZED & ZERO-CLICK AUTONOMY)
# ==========================================
 
import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import json
import requests
import os
 
# --- NASTAVENIE STRÁNCY ---
st.set_page_config(
   page_title="Asistent Štefana Šarközyho - Terénny Systém",
   layout="wide",
   page_icon="💼"
)
 
DB_NAME = "asistent.db"
ALT_CSV_SR = "Seznam kontaktů 01-11-26 17-48-33 PhDr. Šarkőzy.csv"
ALT_CSV_CZ = "Seznam kontaktů 01-11-26 17-49-20 PhDr. Šarkőzy.csv"
 
# --- DATABÁZOVÁ INICIALIZÁCIA ---
def get_connection():
    return sqlite3.connect(DB_NAME)
 
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dopyty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum_vytvorenia TEXT,
            sluzby TEXT,
            hodiny REAL,
            miesto TEXT,
            krajina TEXT,
            datum_akcie TEXT,
            cas TEXT,
            cestovny_cas REAL,
            odchod TEXT,
            cena_sluzby TEXT,
            cena_cestovne REAL,
            ubytovanie REAL,
            strava REAL,
            km INTEGER,
            stav TEXT,
            poznamka TEXT,
            mena TEXT,
            celkova_suma REAL,
            detail_poloziek TEXT,
            navrh_odpovedi TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partneri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ico TEXT,
            dic TEXT,
            nazov TEXT,
            adresa TEXT,
            krajina TEXT,
            zdroj TEXT,
            datum_pridania TEXT
        )
    ''')
 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trasy_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            miesto TEXT,
            den_v_tyzdni INTEGER,
            planovany_cas REAL,
            realny_cas REAL,
            odchylka_minut INTEGER
        )
    ''')
 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vnutorne_faktury (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dopyt_id INTEGER UNIQUE,
            datum_generovania TEXT,
            entita TEXT,
            odberatel TEXT,
            popis_sluzieb TEXT,
            suma_celkom REAL,
            mena TEXT,
            stav_podkladu TEXT,
            json_payload TEXT
        )
    ''')
    conn.commit()
    conn.close()
 
init_db()
 
# --- AUTOMATICKÉ NAČÍTANIE iDoklad CSV SÚBOROV DO DATABÁZY ---
def automaticky_nahrat_partnerov():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM partneri WHERE zdroj = 'iDoklad CSV'")
    
    if os.path.exists(ALT_CSV_SR):
        try:
            df_sr = pd.read_csv(ALT_CSV_SR)
            for _, row in df_sr.iterrows():
                nazov = str(row.get('Firma', '')).strip()
                ico_raw = row.get('IČ', '')
                ico = str(int(ico_raw)) if pd.notna(ico_raw) and str(ico_raw).replace('.0','').isdigit() else str(ico_raw).strip()
                dic = str(row.get('DIČ', row.get('IČ DPH', ''))).strip()
                ulica = str(row.get('Ulice', '')).strip()
                mesto = str(row.get('Město', '')).strip()
                adresa = f"{ulica}, {mesto}".strip(", ")
                
                if nazov and nazov != "nan":
                    cursor.execute('''
                        INSERT INTO partneri (ico, dic, nazov, adresa, krajina, zdroj, datum_pridania)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (ico if ico != "nan" and ico else "000000", dic if dic != "nan" else "", nazov, adresa if adresa else "Slovenská republika", "Slovensko (SR)", "iDoklad CSV", datetime.now().strftime("%Y-%m-%d %H:%M")))
        except Exception:
            pass
 
    if os.path.exists(ALT_CSV_CZ):
        try:
            df_cz = pd.read_csv(ALT_CSV_CZ)
            for _, row in df_cz.iterrows():
                nazov = str(row.get('Firma', '')).strip()
                ico_raw = row.get('IČ', '')
                ico = str(int(ico_raw)) if pd.notna(ico_raw) and str(ico_raw).replace('.0','').isdigit() else str(ico_raw).strip()
                dic = str(row.get('DIČ / IČ DPH', row.get('DIČ', ''))).strip()
                ulica = str(row.get('Ulice', '')).strip()
                mesto = str(row.get('Město', '')).strip()
                adresa = f"{ulica}, {mesto}".strip(", ")
                
                if nazov and nazov != "nan":
                    cursor.execute('''
                        INSERT INTO partneri (ico, dic, nazov, adresa, krajina, zdroj, datum_pridania)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (ico if ico != "nan" and ico else "000000", dic if dic != "nan" else "", nazov, adresa if adresa else "Česká republika", "Česká republika (ČR)", "iDoklad CSV", datetime.now().strftime("%Y-%m-%d %H:%M")))
        except Exception:
            pass
 
    conn.commit()
    conn.close()
 
automaticky_nahrat_partnerov()
 
HOURLY_RATES_EUR = {
    "SI - individuálna supervízia": 55.0,
    "SS - skupinová supervízia": 60.0,
    "KI - krízová intervencia": 60.0,
    "K - koučing": 60.0,
    "V - vzdelávanie": 60.0
}
 
HOURLY_RATES_CZK = {
    "SI - individuálna supervízia": 1375.0,
    "SS - skupinová supervízia": 1500.0,
    "KI - krízová intervencia": 1500.0,
    "K - koučing": 1500.0,
    "V - vzdelávanie": 1500.0
}
 
DISTANCE_DATABASE = {
    "jelka": 90, "kc jelka": 90, "cífer": 100, "piešťany": 160, "cdr piešťany": 160,
    "kc príbeta": 220, "kc šaľa": 130, "dss javorinská": 20, "pezinok": 50,
    "pezinok ospod": 50, "cdr pezinok": 50, "partizánske": 290, "trnava": 90,
    "nitra": 180, "brno": 260, "praha": 660, "bystřice nad pernštejnem": 220, "zlobice": 190
}
 
class DuálnyRegisterClient:
    def nacitaj_partnerov_z_db(self, krajina):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nazov, ico, adresa, dic FROM partneri WHERE krajina = ?", (krajina,))
        rows = cursor.fetchall()
        conn.close()
        return rows
 
class EkonomFinancier:
    def ziskaj_nastavenia_entity(self, krajina_str):
        if "Česká" in krajina_str:
            return {"ico": "09731041", "nazov": "Etien Institut s.r.o. (ČR)", "mena": "CZK", "sym": "Kč"}
        return {"ico": "43289576", "nazov": "PhDr. Štefan Šarközy (SR)", "mena": "EUR", "sym": "€"}
 
    def uloz_do_vnutornej_databazy(self, row_data):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            entita = "Etien Institut s.r.o. (ČR)" if row_data.get('mena') == 'CZK' else "PhDr. Štefan Šarközy (SR)"
            
            payload = {
               "DopytID": row_data.get('id'),
               "Dodávateľ": entita,
               "OdberatelMiesto": row_data.get('miesto'),
               "OdberatelICO": row_data.get('odberatel_ico', ''),
               "OdberatelNazov": row_data.get('odberatel_nazov', ''),
               "Krajina": row_data.get('krajina'),
               "SluzbyPolozky": row_data.get('sluzby_polozky'),
               "SumaZaSluzby": row_data.get('cena_sluzby'),
               "CenaCestovne": row_data.get('cena_cestovne'),
               "Kilometre": row_data.get('km'),
               "DatumAkcie": row_data.get('datum_akcie'),
               "CasAkcie": row_data.get('cas'),
               "CelkovaSuma": row_data.get('celkova_suma'),
               "Mena": row_data.get('mena'),
               "Poznamka": row_data.get('poznamka')
            }
            
            cursor.execute('''
                INSERT OR REPLACE INTO vnutorne_faktury (dopyt_id, datum_generovania, entita, odberatel, popis_sluzieb, suma_celkom, mena, stav_podkladu, json_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
               row_data.get('id'),
               datetime.now().strftime("%Y-%m-%d %H:%M"),
               entita,
               f"{row_data.get('odberatel_nazov', '')} (IČO: {row_data.get('odberatel_ico', '')})",
               row_data.get('sluzby_popis'),
               row_data.get('celkova_suma'),
               row_data.get('mena'),
               'Čaká na spracovanie',
               json.dumps(payload, ensure_ascii=False)
            ))
            conn.commit()
            conn.close()
            return True, "Podklad úspešne uložený!"
        except Exception as e:
            return False, f"Chyba: {str(e)}"
 
# --- AI KOORDINÁTOR (INOVOVANÝ S VYZÝVANÍM A NÁVRHOM ODPOVEDÍ) ---
class EtienAIKoordinator:
    def analyzuj_vstup(self, raw_text):
        txt = raw_text.lower()
        krajina = "Česká republika (ČR)" if any(w in txt for w in ["cesko", "česko", "cz", "praha", "brno", "bystřice", "zlobice"]) else "Slovensko (SR)"
        
        miesto = "Bratislava"
        for m_key in DISTANCE_DATABASE.keys():
            if m_key in txt:
                miesto = m_key.title()
                break

        srv_matches = re.findall(r'(ss|si|ki|k|v)\s*(\d+[\.,]?\d*)\s*h', txt)
        mapping = {
            "ss": "SS - skupinová supervízia",
            "si": "SI - individuálna supervízia",
            "ki": "KI - krízová intervencia",
            "k": "K - koučing",
            "v": "V - vzdelávanie"
        }
        
        polozky = []
        for s_code, h_val in srv_matches:
            try:
                h_num = float(h_val.replace(',', '.'))
            except:
                h_num = 1.0
            polozky.append({"sluzba": mapping.get(s_code, "SI - individuálna supervízia"), "hodiny": h_num})

        chyby = []
        if not miesto or miesto == "Bratislava" and "bratislava" not in txt:
            chyby.append("Miesto konania (mesto)")
        if not polozky:
            chyby.append("Typ služby a počet hodín")

        navrh_odpovedi = ""
        if chyby:
            navrh_odpovedi = f"Dobrý deň, ďakujem za dopyt. Pre potvrdenie termínu a kalkuláciu mi prosím doplňte: {', '.join(chyby)}."

        return {
            "surowy_text": raw_text,
            "krajina": krajina,
            "miesto": miesto,
            "polozky": polozky,
            "chyby": chyby,
            "navrh_odpovedi": navrh_odpovedi
        }

koordinator = EtienAIKoordinator()
 
class DispecerManager:
    def vygeneruj_gcal_url(self, title, date_str, time_str, duration_hours, location, details):
        try:
            start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except Exception:
            start_dt = datetime.now()
        end_dt = start_dt + timedelta(hours=duration_hours)
        
        fmt = "%Y%m%dT%H%M%S"
        params = {
           "action": "TEMPLATE",
           "text": title,
           "dates": f"{start_dt.strftime(fmt)}Z/{end_dt.strftime(fmt)}Z",
           "details": details,
           "location": location
        }
        return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"
 
def clear_form_state():
    keys_to_clear = [
       "vzdialenost_km_val", "cena_cestovne_val", "last_miesto_val", 
       "cas_akcie_input_val", "cas_odchodu_input_val",
       "manual_odberatel_nazov", "manual_odberatel_ico"
    ]
    for k in list(st.session_state.keys()):
        if k.startswith("serv_") or k.startswith("hod_") or k.startswith("cena_") or k in keys_to_clear:
            del st.session_state[k]
 
if "menu_tab" not in st.session_state:
    st.session_state.menu_tab = "Dopyty"
if "edit_item" not in st.session_state:
    st.session_state.edit_item = None
if "last_gcal_url" not in st.session_state:
    st.session_state.last_gcal_url = None
if "service_blocks" not in st.session_state:
    st.session_state.service_blocks = [{"sluzba": "SI - individuálna supervízia", "hodiny": 4.0}]
 
st.markdown("""
    <script>
        var body = window.parent.document.querySelector(".main");
        if (body) {
            body.scrollTop = 0;
        }
        window.scrollTo(0, 0);
    </script>
""", unsafe_allow_html=True)
 
if "theme_choice" not in st.session_state:
    st.session_state.theme_choice = "Bridlicovo-sivá (Slate)"
 
THEMES = {
   "Bridlicovo-sivá (Slate)": {"header_bg": "#0f172a", "card_border": "#0f172a", "accent": "#334155", "bg_color": "#ffffff", "badge_bg": "#f1f5f9"},
    "Hlboká námornícka modrá (Deep Navy)": {"header_bg": "#1e3a8a", "card_border": "#1e3a8a", "accent": "#3b82f6", "bg_color": "#ffffff", "badge_bg": "#eff6ff"},
    "Lesná zelená (Forest Calm)": {"header_bg": "#064e3b", "card_border": "#064e3b", "accent": "#059669", "bg_color": "#ffffff", "badge_bg": "#ecfdf5"},
    "Kráľovská purpurová (Royal Burgundy)": {"header_bg": "#581c87", "card_border": "#581c87", "accent": "#9333ea", "bg_color": "#ffffff", "badge_bg": "#faf5ff"},
    "Jantárová jeseň (Amber Bronze)": {"header_bg": "#78350f", "card_border": "#78350f", "accent": "#d97706", "bg_color": "#ffffff", "badge_bg": "#fffbeb"},
    "Polnočný OLED (Cyber Dark)": {"header_bg": "#09090b", "card_border": "#27272a", "accent": "#06b6d4", "bg_color": "#18181b", "badge_bg": "#27272a"},
    "Svetlý terénny kontrast (Outdoor High-Vis)": {"header_bg": "#0284c7", "card_border": "#0369a1", "accent": "#0284c7", "bg_color": "#f8fafc", "badge_bg": "#e0f2fe"}
}
 
current_theme = THEMES[st.session_state.theme_choice]
 
st.markdown(f"""
    <style>
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button {{ 
        -webkit-appearance: none; 
        margin: 0; 
    }}
    input[type=number] {{
        -moz-appearance: textfield;
    }}
    .stButton>button {{
        width: 100%;
        min-height: 48px;
        font-size: 16px !important;
        font-weight: 600;
        border-radius: 8px;
        margin-top: 6px;
        margin-bottom: 6px;
    }}
    .stSelectbox div[data-baseweb="select"], .stTextInput input, .stNumberInput input {{
        min-height: 46px !important;
        font-size: 16px !important;
    }}
    label {{
        font-size: 15px !important;
        font-weight: 500 !important;
        color: #1e293b !important;
    }}
    .card {{
        background-color: {current_theme['bg_color']};
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        border: 2px solid #cbd5e1;
        border-left: 6px solid {current_theme['card_border']};
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .idoklad-partner-card {{
        background-color: {current_theme['badge_bg']};
        padding: 18px;
        border-radius: 10px;
        border: 2px solid #cbd5e1;
        border-left: 6px solid {current_theme['accent']};
        margin-top: 12px;
        margin-bottom: 18px;
    }}
    </style>
""", unsafe_allow_html=True)
 
st.markdown(f"""
    <div style="background-color: {current_theme['header_bg']}; color: white; padding: 22px 24px; border-radius: 12px; margin-bottom: 20px;">
        <h1 style="margin: 0; color: white; font-size: 24px;">💼 Asistent Štefana Šarközyho</h1>
        <p style="margin: 6px 0 0 0; color: #94a3b8; font-size: 13px;">🟢 Duálny terénny systém s AI Koordinátorom (SR & ČR)</p>
    </div>
""", unsafe_allow_html=True)
 
# --- CENTRÁLNA PRÍKAZOVÁ KONZOLA (COMMAND PALETTE) ---
cmd_input = st.text_input("⚡ Centrálny príkazový riadok (napr. /vstup, /cakat, /faktura):", placeholder="Zadaj príkaz pre Koordinátora...")
if cmd_input.startswith("/"):
    if "/cakat" in cmd_input:
        st.session_state.menu_tab = "Čakajúce na doplnenie"
        st.rerun()
    elif "/faktura" in cmd_input:
        st.session_state.menu_tab = "Vnútorná fakturácia"
        st.rerun()
    elif "/vstup" in cmd_input:
        st.session_state.menu_tab = "Nová / Úprava výjazdu"
        st.rerun()

# Kontrola neúplných záznamov (Notifikácia od Koordinátora)
conn = get_connection()
df_neuplne = pd.read_sql("SELECT * FROM dopyty WHERE stav = 'Čaká na doplnenie'", conn)
conn.close()

if not df_neuplne.empty:
    st.markdown(f"""
        <div style="background-color: #fffbeb; border: 2px solid #f59e0b; padding: 15px; border-radius: 10px; margin-bottom: 15px; color: #92400e;">
            <h4 style="margin:0 0 5px 0;">⚠️ Úloha od Koordinátora:</h4>
            <p style="margin:0;">Máte <b>{len(df_neuplne)}</b> dopytov z SMS / WhatsApp, ktoré vyžadujú vaše doplnenie!</p>
        </div>
    """, unsafe_allow_html=True)

col_th1, col_th2 = st.columns([3, 1])
with col_th1:
    tabs_options = ["Dopyty", "Čakajúce na doplnenie", "Nová / Úprava výjazdu", "Správa partnerov", "Vnútorná fakturácia", "Simulátor AI", "Inovácie"]
    if st.session_state.menu_tab not in tabs_options:
        st.session_state.menu_tab = "Dopyty"
    selected_tab = st.radio("Navigácia", tabs_options, index=tabs_options.index(st.session_state.menu_tab), horizontal=True, label_visibility="collapsed")
    if selected_tab != st.session_state.menu_tab:
        st.session_state.menu_tab = selected_tab
        st.rerun()
with col_th2:
    new_theme = st.selectbox("🎨 Dizajnér tém", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme_choice))
    if new_theme != st.session_state.theme_choice:
        st.session_state.theme_choice = new_theme
        st.rerun()
 
st.divider()
 
# ==========================================
# 1. ZÁLOŽKA: DOPYTY
# ==========================================
if st.session_state.menu_tab == "Dopyty":
    st.header("📋 Zoznam zaznamenaných dopytov a výjazdov")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM dopyty WHERE stav != 'Čaká na doplnenie'", conn)
    conn.close()
    
    search_query = st.text_input("🔍 Vyhľadávanie v dopytoch (miesto, služba, poznámka)", "").strip().lower()
    if search_query:
        df = df[
           df["miesto"].str.lower().str.contains(search_query, na=False) |
           df["sluzby"].str.lower().str.contains(search_query, na=False) |
           df["poznamka"].str.lower().str.contains(search_query, na=False)
        ]
 
    if df.empty:
        st.info("Zatiaľ žiadne záznamy.")
    else:
        for idx, row in df.iterrows():
            mena = row.get('mena', 'EUR')
            sym = "Kč" if mena == "CZK" else "€"
            record_id = row.get('id')
            
            c_info, c_btn1, c_btn2 = st.columns([3.3, 1, 1])
            with c_info:
                st.markdown(f"""
                    <div class='card'>
                        <h4>#{record_id} - {row['sluzby']} ({row['miesto']}, {row['krajina']}) [Mena: {mena}]</h4>
                        <p><b>Termín:</b> {row['datum_akcie']} o {row['cas']} | <b>Rozsah:</b> {row['hodiny']} hod. | <b>Spolu:</b> {row['celkova_suma']} {sym}</p>
                        <p><i>{row['poznamka']}</i></p>
                    </div>
                """, unsafe_allow_html=True)
            with c_btn1:
                st.write("")
                if st.button("📅 Spracovať", key=f"btn_proc_{record_id}_{idx}"):
                    clear_form_state()
                    st.session_state.edit_item = row.to_dict()
                    srv_str = row['sluzby']
                    parts = [p.strip() for p in str(srv_str).split("+")]
                    total_h = float(row['hodiny'])
                    h_per = total_h / max(1, len(parts))
                    rates = HOURLY_RATES_CZK if row.get('krajina') == "Česká republika (ČR)" else HOURLY_RATES_EUR
                    all_srv = list(rates.keys())
                    st.session_state.service_blocks = [{"sluzba": p if p in all_srv else all_srv[0], "hodiny": h_per} for p in parts]
                    st.session_state.menu_tab = "Nová / Úprava výjazdu"
                    st.rerun()
            with c_btn2:
                st.write("")
                if st.button("🗑️ Vymazať", key=f"btn_del_{record_id}_{idx}"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    if pd.notna(record_id):
                        cursor.execute("DELETE FROM dopyty WHERE id = ?", (record_id,))
                        cursor.execute("DELETE FROM vnutorne_faktury WHERE dopyt_id = ?", (record_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"Dopyt #{record_id} a fakturačný podklad boli vymazané.")
                    st.rerun()

# ==========================================
# 1.1 ZÁLOŽKA: ČAKAJÚCE NA DOPLNENIE (AI KOORDINÁTOR)
# ==========================================
elif st.session_state.menu_tab == "Čakajúce na doplnenie":
    st.header("⏳ Záznamy čakajúce na doplnenie (Úlohy od Koordinátora)")
    st.markdown("Tu sú zachytené správy z SMS / WhatsApp, ktoré vyžadujú vaše schválenie alebo doplnenie údajov.")
    
    conn = get_connection()
    df_c = pd.read_sql("SELECT * FROM dopyty WHERE stav = 'Čaká na doplnenie'", conn)
    conn.close()
    
    if df_c.empty:
        st.success("Žiadne záznamy nečakajú na doplnenie. Všetko je hotové!")
    else:
        for idx, row in df_c.iterrows():
            st.markdown(f"""
                <div class='card' style="border-left-color: #f59e0b;">
                    <h4>Záznam #{row['id']} ({row['datum_vytvorenia']})</h4>
                    <p><b>Pôvodná správa / dopyt:</b> {row['sluzby']}</p>
                    <p><b>Problém:</b> <span style="color: #b45309;">{row['poznamka']}</span></p>
                    <p><b>💬 Návrh odpovedi pre klienta od Koordinátora:</b> <br><i>{row['navrh_odpovedi']}</i></p>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"✏️ Dokončiť a schváliť záznam #{row['id']}", key=f"dokoncit_{row['id']}"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE dopyty SET stav = 'Kalendár', poznamka = 'Dokončené na základe výzvy Koordinátora' WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                st.success(f"Záznam #{row['id']} bol úspešne dokončený a presunutý do výjazdov!")
                st.rerun()
 
# ==========================================
# 2. ZÁLOŽKA: NOVÁ / ÚPRAVA VÝJAZDU
# ==========================================
elif st.session_state.menu_tab == "Nová / Úprava výjazdu":
    item = st.session_state.edit_item
    if item:
        st.header(f"⚙️ Úprava dopytu #{item['id']} ({item['miesto']})")
    else:
        st.header("➕ Nový výjazd / SMS Dispečer")
        
        # Rýchly AI vstup pre Koordinátora (Inovácia zo Zapieru / Superhuman)
        st.markdown("""
            <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border: 2px dashed #0284c7; padding: 15px; border-radius: 12px; margin-bottom: 15px;">
                <h4 style="margin: 0 0 5px 0; color: #0369a1; font-size: 15px;">🎙️ Automatické spracovanie cez AI Koordinátora</h4>
                <p style="margin: 0; font-size: 12px; color: #475569;">Vložte text z SMS / WhatsAppu a Koordinátor predvyplní formulár za vás, overí dáta a pripraví odpoveď.</p>
            </div>
        """, unsafe_allow_html=True)
        
        ai_raw_input = st.text_input("Vložte text správy od klienta:", value="", placeholder="Napr. Brno ss 3h...")
        if st.button("🤖 Nechať Koordinátora predvyplniť"):
            if ai_raw_input.strip():
                res = koordinator.analyzuj_vstup(ai_raw_input)
                if res["chyby"]:
                    st.warning(f"Koordinátor hlási neúplné údaje: {', '.join(res['chyby'])}")
                    st.info(f"Návrh odpovedi: {res['navrh_odpovedi']}")
                else:
                    st.success("Koordinátor úspešne analyzoval dopyt!")
 
    def_krajina = item['krajina'] if item and 'krajina' in item else "Slovensko (SR)"
    def_miesto = item['miesto'] if item and 'miesto' in item else ""
    def_cesta = float(item.get('cestovny_cas', 1.0)) if item else 1.0
 
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        krajina = st.radio("Základ / Krajina výjazdu", ["Slovensko (SR)", "Česká republika (ČR)"], horizontal=True, index=0 if def_krajina=="Slovensko (SR)" else 1, key="krajina_radio_key")
    with col_l2:
        pass
 
    comp = EkonomFinancier().ziskaj_nastavenia_entity(krajina)
    mena = comp["mena"]
    sym = comp["sym"]
 
    if krajina == "Česká republika (ČR)":
        active_rates = HOURLY_RATES_CZK
        def_amort = 5.60
        def_palivo = 38.50
        def_sadzba_casy = 375.0
    else:
        active_rates = HOURLY_RATES_EUR
        def_amort = 0.313
        def_palivo = 1.95
        def_sadzba_casy = 15.0
 
    all_srv_list = list(active_rates.keys())
 
    st.info(f"🌐 **Aktivovaný kontext:** Dodávateľ: **{comp['nazov']}** | Mena: **{mena}**")
 
    st.markdown("---")
    st.subheader(f"🏢 Miesto konania a fakturačný odberateľ ({krajina})")
 
    register_client = DuálnyRegisterClient()
    saved_partners = register_client.nacitaj_partnerov_z_db(krajina)
 
    známe_miesta = ["-- Vyberte miesto konania --", "KC Jelka", "Cífer", "Piešťany", "KC Príbeta", "KC Šaľa", "DSS Javorinská", "Pezinok", "Partizánske", "Trnava", "Nitra", "Brno", "Praha"]
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("📍 **1. Miesto konania (pre výpočet km)**")
        vybrane_miesto_box = st.selectbox("Známe miesto / trasa", známe_miesta, key="logika_miesto_box")
        manualne_miesto = st.text_input("Alebo napíšte miesto konania priamo", value=def_miesto, key="logika_manual_miesto")
    
    with col_m2:
        st.markdown("🏢 **2. Organizácia / iDoklad výber**")
        partner_zoznam = ["-- Vyberte zo saved / iDokladu --"] + [f"{p[0]} (IČO: {p[1]})" for p in saved_partners]
        vybrany_partner_box = st.selectbox("Uložený partner v DB", partner_zoznam, key="logika_partner_box")
 
    miesto = ""
    if manualne_miesto.strip():
        miesto = manualne_miesto.strip()
    elif vybrane_miesto_box != známe_miesta[0]:
        miesto = vybrane_miesto_box
    else:
        miesto = def_miesto if def_miesto else "Neznáme miesto"
 
    st.markdown("✍️ **Ručné zadanie údajov pre faktúru (má prednosť pred výberom)**")
    rc1, rc2 = st.columns(2)
    with rc1:
        manual_odberatel_nazov = st.text_input("Fakturačný odberateľ (Názov firmy / Inštitúcie)", value="", key="manual_odberatel_nazov", placeholder="Napr. Asociácia supervízorov...")
    with rc2:
        manual_odberatel_ico = st.text_input("IČO odberateľa", value="", key="manual_odberatel_ico", placeholder="Napr. 31803989")
 
    odberatel_nazov = miesto
    odberatel_ico = ""
    odberatel_adresa = "Slovenská republika" if "Slovensko" in krajina else "Česká republika"
 
    if vybrany_partner_box and vybrany_partner_box != partner_zoznam[0]:
        zvoleny_nazov = vybrany_partner_box.split(" (IČO:")[0].strip()
        for p in saved_partners:
            if str(p[0]).strip() == zvoleny_nazov:
                odberatel_nazov = p[0]
                odberatel_ico = str(p[1]) if pd.notna(p[1]) and str(p[1]) != "nan" else ""
                odberatel_adresa = str(p[2]) if pd.notna(p[2]) and str(p[2]) != "nan" and str(p[2]).strip() != "," else odberatel_adresa
                break
 
    if manual_odberatel_nazov.strip():
        odberatel_nazov = manual_odberatel_nazov.strip()
    if manual_odberatel_ico.strip():
        odberatel_ico = manual_odberatel_ico.strip()
 
    if miesto:
        lookup_key = miesto.lower()
        for k_db, km_val in DISTANCE_DATABASE.items():
            if k_db in lookup_key:
                st.session_state["vzdialenost_km_val"] = km_val
                break
 
    st.markdown(f"""
        <div class="idoklad-partner-card">
            <h4 style="margin: 0 0 8px 0; color: #0f172a;">📋 Súhrn výjazdu a fakturačné údaje</h4>
            <p style="margin: 4px 0;">📍 <b>Miesto konania:</b> <code>{miesto}</code></p>
            <p style="margin: 4px 0;">🏢 <b>Fakturačný odberateľ:</b> {odberatel_nazov}</p>
            <p style="margin: 4px 0;">🆔 <b>IČO:</b> {odberatel_ico if odberatel_ico else 'Neuvedené'}</p>
            <p style="margin: 4px 0;">🏠 <b>Sídlo:</b> {odberatel_adresa}</p>
        </div>
    """, unsafe_allow_html=True)
 
    lookup_key = miesto.strip().lower()
    auto_km = DISTANCE_DATABASE.get(lookup_key, int(item.get('km', 660 if krajina == "Česká republika (ČR)" else 60)) if item else (660 if krajina == "Česká republika (ČR)" else 60))
    
    if "last_miesto_val" not in st.session_state or st.session_state.get("last_miesto_val") != miesto:
        st.session_state["last_miesto_val"] = miesto
        if "vzdialenost_km_val" not in st.session_state:
            st.session_state["vzdialenost_km_val"] = auto_km
 
    st.markdown("---")
    st.markdown(f"### Služby a položky ({mena})")
 
    total_sluzba_cena, total_hodiny = 0.0, 0.0
    updated_blocks = []
    polozky_pre_fakturu = []
 
    for idx, block in enumerate(st.session_state.service_blocks):
        cb1, cb2, cb3, cb4, cb5 = st.columns([2.8, 1.2, 1.2, 0.9, 0.9])
        with cb1:
            curr_s = block["sluzba"]
            if curr_s not in all_srv_list:
                curr_s = all_srv_list[0]
            sel_s = st.selectbox(f"Služba {idx+1}", all_srv_list, index=all_srv_list.index(curr_s), key=f"serv_{idx}")
        with cb2:
            sel_h = st.number_input(f"Hodiny {idx+1}", min_value=0.5, max_value=50.0, value=float(block["hodiny"]), step=0.5, key=f"hod_{idx}", format="%.1f")
        
        default_rate = active_rates.get(sel_s, 55.0)
        with cb3:
            sel_rate = st.number_input(f"Cena/1h {idx+1} ({sym})", min_value=0.0, max_value=10000.0, value=float(default_rate), step=5.0, key=f"rate_{idx}")
 
        calc_price = round(sel_h * sel_rate, 2)
        with cb4:
            st.write("")
            st.write(f"**{calc_price} {sym}**")
        with cb5:
            st.write("")
            conf_clicked = st.button("✅ OK", key=f"conf_{idx}")
            if len(st.session_state.service_blocks) > 1 and st.button("🗑️", key=f"del_{idx}"):
                st.session_state.service_blocks.pop(idx)
                st.rerun()
 
        total_sluzba_cena += calc_price
        total_hodiny += sel_h
        updated_blocks.append({"sluzba": sel_s, "hodiny": sel_h, "cena_za_1h": sel_rate, "spolu": calc_price})
        polozky_pre_fakturu.append(f"- {sel_s} : počet hodín: {sel_h} hod.    cena za 1h: {sel_rate} {mena} (Spolu: {calc_price} {mena})")
        st.divider()
 
    st.session_state.service_blocks = updated_blocks
    if st.button("+ Pridať ďalšiu službu / blok"):
        st.session_state.service_blocks.append({"sluzba": all_srv_list[0], "hodiny": 1.0})
        st.rerun()
 
    st.markdown("---")
    st.markdown("### 📅 Dátum a čas konania akcie")
    
    try:
        def_date = datetime.strptime(str(item['datum_akcie']), "%Y-%m-%d").date() if item and pd.notna(item.get('datum_akcie')) else datetime.now().date()
    except Exception:
        def_date = datetime.now().date()
 
    datum_akcie = st.date_input("Dátum konania akcie", value=def_date, key="datum_akcie_input")
 
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        def_cas_akcie = item.get('cas', '09:00') if item and pd.notna(item.get('cas')) else '09:00'
        cas_akcie_str = st.text_input("Čas akcie (napr. 09:00)", value=def_cas_akcie, key="cas_akcie_input_val")
    with col_t2:
        def_cas_odchodu = item.get('odchod', '08:00') if item and pd.notna(item.get('odchod')) else '08:00'
        cas_odchodu_str = st.text_input("Čas odchodu (napr. 08:00)", value=def_cas_odchodu, key="cas_odchodu_input_val")
 
    st.markdown("---")
    st.markdown(f"### 🚗 KALKULÁTOR CESTOVNÉHO ({sym})")
    
    ck1, ck2, ck3, ck4 = st.columns(4)
    with ck1:
        vzdialenost_km = st.number_input("Kilometre tam a späť (km)", min_value=0, max_value=3000, step=10, key="vzdialenost_km_val")
    with ck2:
        spotreba = st.number_input("Spotreba (l/100 km)", min_value=1.0, max_value=20.0, value=8.5, step=0.1, key="spotreba_key")
    with ck3:
        cena_paliva = st.number_input(f"Cena paliva ({sym}/l)", min_value=0.5, max_value=100.0, value=def_palivo, step=0.05, key="cena_paliva_key")
    with ck4:
        amortizacia_rate = st.number_input(f"Amortizácia ({sym}/km)", min_value=0.01, max_value=50.0, value=def_amort, step=0.001, format="%.3f", key="amort_key")
 
    cc1, cc2 = st.columns(2)
    with cc1:
        cestovny_cas = st.number_input("Cestovný čas (hod.)", min_value=0.0, max_value=10.0, value=def_cesta, step=0.5, key="cestovny_cas_key")
    with cc2:
        sadzba_casy = st.number_input(f"Sadzba za cestovný čas ({sym}/hod)", min_value=0.0, max_value=2000.0, value=def_sadzba_casy, step=1.0, key="sadzba_casy_key")
 
    vypocitane_amortizacia = vzdialenost_km * amortizacia_rate
    vypocitane_palivo = (spotreba / 100.0) * vzdialenost_km * cena_paliva
    vypocitane_cas = cestovny_cas * sadzba_casy
    
    auto_cest = round(vypocitane_amortizacia + vypocitane_palivo + vypocitane_cas, 2)
    st.session_state["cena_cestovne_val"] = auto_cest
 
    cena_cestovne = st.number_input(f"Cestovne spolu ({sym})", min_value=0.0, max_value=50000.0, step=5.0, key="cena_cestovne_val")
 
    celkova_suma = round(float(total_sluzba_cena) + float(cena_cestovne), 2)
    st.markdown(f"""
        <div style='background-color: #f1f5f9; padding: 18px; border-radius: 10px; border: 2px solid #334155; margin: 20px 0;'>
            <h3 style='margin: 0; color: #0f172a;'>Celková suma k úhrade: <b>{celkova_suma} {sym}</b></h3>
            <p style='margin: 5px 0 0 0; color: #475569; font-size: 13px;'>Dodávateľ: <b>{comp['nazov']}</b> (IČO: {comp['ico']}) | Služby: {total_sluzba_cena:.2f} {sym} + Cestovné: {cena_cestovne:.2f} {sym}</p>
        </div>
    """, unsafe_allow_html=True)
 
    poznamka = st.text_area("Poznámka / Interné detaily", value=item.get('poznamka', '') if item else "")
    combined_services_str = " + ".join([b["sluzba"] for b in st.session_state.service_blocks])
 
    if st.session_state.get("last_gcal_url"):
        st.success("Termín pripravený pre Google Kalendár:")
        st.link_button("📅 Otvoriť a pridať do Google Kalendára", st.session_state.last_gcal_url)
 
    btn_label = f"💾 Uložiť výjazd a preniesť do vnútornej fakturácie ({comp['nazov']})" if item else "💾 Uložiť výjazd do kalendára a databázy"
    if st.button(btn_label, type="primary"):
        gcal_details = f"Entita: {comp['nazov']} (IČO: {comp['ico']})\nCelkom: {celkova_suma} {sym}"
        gcal_url = DispecerManager().vygeneruj_gcal_url(
            f"{combined_services_str} ({miesto})", str(datum_akcie), cas_akcie_str, total_hodiny, f"{miesto}, {krajina}", gcal_details
        )
        st.session_state.last_gcal_url = gcal_url
 
        conn = get_connection()
        cursor = conn.cursor()
        if item:
            cursor.execute('''
                UPDATE dopyty SET
                    sluzby = ?, hodiny = ?, miesto = ?, krajina = ?, datum_akcie = ?,
                    cas = ?, cestovny_cas = ?, odchod = ?, cena_sluzby = ?, cena_cestovne = ?,
                    ubytovanie = ?, strava = ?, km = ?, poznamka = ?, mena = ?, celkova_suma = ?, detail_poloziek = ?, stav = 'Kalendár'
                WHERE id = ?
            ''', (
                combined_services_str, total_hodiny, miesto, krajina, str(datum_akcie),
                cas_akcie_str, cestovny_cas, cas_odchodu_str, str(total_sluzba_cena), float(cena_cestovne),
                0.0, 0.0, int(vzdialenost_km), poznamka, mena, float(celkova_suma),
                json.dumps(updated_blocks, ensure_ascii=False), item['id']
            ))
            dopyt_id_val = item['id']
        else:
            cursor.execute('''
                INSERT INTO dopyty (
                    datum_vytvorenia, sluzby, hodiny, miesto, krajina, datum_akcie, cas, 
                    cestovny_cas, odchod, cena_sluzby, cena_cestovne, ubytovanie, strava, 
                    km, stav, poznamka, mena, celkova_suma, detail_poloziek
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Kalendár', ?, ?, ?, ?)
            ''', (
                datetime.now().strftime("%Y-%m-%d %H:%M"), combined_services_str, total_hodiny, miesto, krajina, str(datum_akcie), cas_akcie_str,
                cestovny_cas, cas_odchodu_str, str(total_sluzba_cena), float(cena_cestovne), 0.0, 0.0,
                int(vzdialenost_km), poznamka, mena, float(celkova_suma), json.dumps(updated_blocks, ensure_ascii=False)
            ))
            dopyt_id_val = cursor.lastrowid
        conn.commit()
        conn.close()
 
        temp_row_data = {
            "id": dopyt_id_val,
            "mena": mena,
            "miesto": miesto,
            "krajina": krajina,
            "odberatel_ico": odberatel_ico,
            "odberatel_nazov": odberatel_nazov,
            "sluzby_polozky": updated_blocks,
            "sluzby_popis": "\n".join(polozky_pre_fakturu),
            "cena_sluzby": total_sluzba_cena,
            "cena_cestovne": cena_cestovne,
            "km": vzdialenost_km,
            "datum_akcie": str(datum_akcie),
            "cas": cas_akcie_str,
            "celkova_suma": celkova_suma,
            "poznamka": poznamka
        }
        EkonomFinancier().uloz_do_vnutornej_databazy(temp_row_data)
 
        st.success("Záznam bol úspešne uložený a pripravený vo vnútornej fakturácii!")
        st.rerun()

# ==========================================
# 3. ZÁLOŽKA: SPRÁVA PARTNEROV
# ==========================================
elif st.session_state.menu_tab == "Správa partnerov":
    st.header("👥 Správa a prehľad partnerov z iDoklad CSV")
    conn = get_connection()
    df_p = pd.read_sql("SELECT * FROM partneri", conn)
    conn.close()
    if df_p.empty:
        st.info("Žiadni partneri v databáze.")
    else:
        st.dataframe(df_p, use_container_width=True)

# ==========================================
# 4. ZÁLOŽKA: VNÚTORNÁ FAKTURÁCIA
# ==========================================
elif st.session_state.menu_tab == "Vnútorná fakturácia":
    st.header("🧾 Vnútorná fakturácia & Podklady")
    conn = get_connection()
    df_f = pd.read_sql("SELECT * FROM vnutorne_faktury", conn)
    conn.close()
    if df_f.empty:
        st.info("Žiadne fakturačné podklady.")
    else:
        for _, r in df_f.iterrows():
            st.markdown(f"""
                <div class='card'>
                    <h4>Podklad pre dopyt #{r['dopyt_id']} ({r['entita']})</h4>
                    <p><b>Odberateľ:</b> {r['odberatel']} | <b>Suma:</b> {r['suma_celkom']} {r['mena']} | <b>Stav:</b> {r['stav_podkladu']}</p>
                </div>
            """, unsafe_allow_html=True)
            with st.expander(f"Zobraziť JSON pre dopyt #{r['dopyt_id']}"):
                st.text(r['popis_sluzieb'])
                st.code(r['json_payload'], language="json")

# ==========================================
# 5. ZÁLOŽKA: SIMULÁTOR AI
# ==========================================
elif st.session_state.menu_tab == "Simulátor AI":
    st.header("🤖 Testovací Simulátor AI Koordinátora")
    sim_text = st.text_input("Zadajte textovú správu pre simuláciu:", placeholder="Napr. Brno ss 3h...")
    if st.button("Spustiť analýzu"):
        res = koordinator.analyzuj_vstup(sim_text)
        st.json(res)

# ==========================================
# 6. ZÁLOŽKA: INOVÁCIE
# ==========================================
elif st.session_state.menu_tab == "Inovácie":
    st.header("💡 Inovácie a budúci rozvoj systému")
    st.markdown("Tu budú pribúdať pokročilé moduly a prepojenia na ďalšie autonómne vrstvy.")