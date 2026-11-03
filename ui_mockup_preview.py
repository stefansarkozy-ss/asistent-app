import streamlit as st

st.set_page_config(
    page_title="Visual UI Mockup Preview",
    layout="wide",
    page_icon="🎨",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #f1f5f9;
        font-family: sans-serif;
    }
    
    /* Presný blok podľa nákresu: tmavomodrý vonkajší box */
    .module-card {
        background-color: #1e3a8a;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        border: 1px solid #3b82f6;
    }
    
    .module-header {
        font-size: 16px;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Biele riadky vo vnútri tmavej karty (presne ako v nákrese) */
    .input-row {
        background-color: #ffffff;
        color: #0f172a;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 10px;
        font-weight: 600;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .input-row-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 10px;
    }
    
    .sub-input {
        background-color: #ffffff;
        color: #0f172a;
        padding: 12px 16px;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='color: #0f172a;'>🎨 Presný náhľad podľa nákresu (navrh 2)</h2>", unsafe_allow_html=True)
st.write("<p style='color: #475569;'>Tmavomodrý blok a biele riadky priamo vo vnútri.</p>", unsafe_allow_html=True)
st.divider()

# 1. MODUL: LOKALIZÁCIA
st.markdown("""
<div class="module-card">
    <div class="module-header">📍 Miesto a lokalizácia</div>
    <div class="input-row">
        <span>Krajina výjazdu: Slovensko (SR)</span>
    </div>
    <div class="input-row">
        <span>Miesto / Obec: CDR Piešťany</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. MODUL: SLUŽBY A BLOKY
st.markdown("""
<div class="module-card">
    <div class="module-header">💼 Služby a bloky</div>
    <div class="input-row">
        <span>Služba: SI - individuálna supervízia</span>
        <span>4.0 hod. | 220.00 €</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. MODUL: KROKOVANIE
st.markdown("""
<div class="module-card">
    <div class="module-header">📅 Dátum a časové krokovanie</div>
    <div class="input-row-grid">
        <div class="sub-input">Deň: 26.10.2026</div>
        <div class="sub-input">Mesiac / Rok: 10 / 2026</div>
    </div>
    <div class="input-row-grid">
        <div class="sub-input">Akcia: 09:00</div>
        <div class="sub-input">Odchod: 08:30</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4. MODUL: CESTOVNÉ
st.markdown("""
<div class="module-card">
    <div class="module-header">🚗 Kalkulátor Cestovného Náhrady</div>
    <div class="input-row">
        <span>Kilometre: 190 km | Spotreba: 8.5 l</span>
    </div>
    <div class="input-row" style="background-color: #0f172a; color: #38bdf8; justify-content: flex-end; border: 1px solid #38bdf8;">
        <span><b>Celková suma na FA: 333.46 €</b></span>
    </div>
</div>
""", unsafe_allow_html=True)