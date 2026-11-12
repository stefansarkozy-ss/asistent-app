# ==========================================
# app.py - ETIENs NEUROSURGICAL ULTIMATE (2026)
# ==========================================

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from databaze import get_connection, init_all_tables, vloz_dopyt
from validator import EtienAsistentValidator

# 1. KONFIGURÁCIA STRÁNKY
st.set_page_config(
    page_title="ETIENs Neurosystém | Autonómny Dirigent Praxe",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. NEURONÁLNY VIP DIZAJN (Glassmorphism & Cyber-Dark)
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #050811 0%, #0f172a 100%);
        border-right: 1px solid rgba(56, 189, 248, 0.2);
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
    .neuro-banner {
        background: linear-gradient(135deg, #090d16 0%, #1e1b4b 50%, #0369a1 100%);
        padding: 2rem;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(56, 189, 248, 0.4);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .neuro-card {
        background: rgba(30, 41, 59, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.4rem;
        border-radius: 12px;
        margin-bottom: 1.2rem;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .prediction-card {
        background: #f8fafc;
        border-left: 5px solid #0284c7;
        padding: 1.1rem;
        border-radius: 10px;
        margin-bottom: 0.9rem;
        color: #0f172a;
    }
    .alert-card {
        background: #fef2f2;
        border-left: 5px solid #dc2626;
        padding: 1.1rem;
        border-radius: 10px;
        margin-bottom: 0.9rem;
        color: #7f1d1d;
    }
    </style>
""", unsafe_allow_html=True)

init_all_tables()

try:
    from moduly import dopyty_modul, vyjazd_modul, fakturacia_modul
    MODULY_OK = True
except ImportError as e:
    MODULY_OK = False
    IMPORT_ERROR_MSG = str(e)


class EtienNeurosytemConductor:
    """
    Autonómny, samoučiaci, samoopravovací a samovylepšujúci neurosystém ETIENs:
    - Riadi tok dát, lieči anomálie a optimalizuje vyťaženie.
    - Vykonáva hĺbkovú psychohygienickú a štatistickú analýzu (hodiny, služby, výnosy, km) v cykloch.
    """
    def __init__(self):
        self.validator = EtienAsistentValidator()

    def self_heal_and_optimize(self) -> dict:
        fixes_report = {"invoices_fixed": 0, "status": "OPTIMAL"}
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            missing = pd.read_sql("""
                SELECT d.* FROM dopyty d
                LEFT JOIN vnutorne_faktury f ON d.id = f.dopyt_id
                WHERE (d.stav LIKE '%SCHVÁLENÉ%' OR d.stav LIKE '%SCHVALENE%') AND f.id IS NULL
            """, conn)

            for _, r in missing.iterrows():
                mena = r['mena'] if 'mena' in r and r['mena'] else 'EUR'
                entita = "ETIENs Institut s.r.o. (ČR)" if mena == 'CZK' else "PhDr. Štefan Šarközy (SR)"
                odberatel = r['miesto'] if 'miesto' in r and r['miesto'] else "Klient"
                suma = float(r['celkova_suma'] or 0.0)
                hodiny_v = float(r['hodiny'] or 6.0)
                sluzba_t = r['sluzby'] if 'sluzby' in r and r['sluzby'] else 'Supervízia'
                
                popis = f"• {sluzba_t} ({r.get('datum_akcie', '')}): {hodiny_v} hod."
                payload = json.dumps({
                    "OdberatelNazov": odberatel,
                    "OdberatelMiesto": odberatel,
                    "DatumAkcie": r.get('datum_akcie', datetime.now().strftime("%Y-%m-%d")),
                    "SumaZaSluzby": suma,
                    "Kilometre": float(r.get('km', 0) or 0.0),
                    "Krajina": "ČR" if mena == "CZK" else "SR",
                    "Poznamka": r.get('poznamka', '') or "Autonómne zosynchronizované Neurosystémom ETIENs."
                }, ensure_ascii=False)

                cursor.execute("""
                    INSERT INTO vnutorne_faktury (dopyt_id, datum_generovania, entita, odberatel, popis_sluzieb, suma_celkom, mena, stav_podkladu, json_payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'SCHVÁLENÉ (NEURO-SYNC)', ?)
                """, (r['id'], datetime.now().strftime("%Y-%m-%d %H:%M"), entita, odberatel, popis, suma, mena, payload))
                fixes_report["invoices_fixed"] += 1

            conn.commit()
            conn.close()
        except Exception as e:
            fixes_report["status"] = f"CHYBA: {str(e)}"
        
        return fixes_report

    def get_period_stats(self, start_date_str: str, end_date_str: str) -> dict:
        stats = {"hodiny": 0.0, "sluzby": 0, "eur": 0.0, "czk": 0.0, "km": 0.0}
        try:
            conn = get_connection()
            df = pd.read_sql("""
                SELECT hodiny, celkova_suma, mena, km 
                FROM dopyty 
                WHERE datum_akcie BETWEEN ? AND ?
            """, conn, params=(start_date_str, end_date_str))
            conn.close()

            if not df.empty:
                stats["hodiny"] = float(df['hodiny'].sum() or 0.0)
                stats["sluzby"] = int(df.shape[0])
                stats["km"] = float(df['km'].sum() or 0.0)
                
                eur_df = df[df['mena'] == 'EUR']
                czk_df = df[df['mena'] == 'CZK']
                stats["eur"] = float(eur_df['celkova_suma'].sum() or 0.0)
                stats["czk"] = float(czk_df['celkova_suma'].sum() or 0.0)
        except Exception:
            pass
        return stats

    def comprehensive_psychohygiene_audit(self) -> dict:
        report = {}
        try:
            today = datetime.now().date()
            
            w_start = today.strftime("%Y-%m-%d")
            w_end = (today + timedelta(days=7)).strftime("%Y-%m-%d")
            w_stats = self.get_period_stats(w_start, w_end)
            report["weekly"] = {**w_stats, "limit": 32.0, "status": "PRETÍŽENIE" if w_stats["hodiny"] > 32.0 else "V NORME"}

            m_start = today.replace(day=1).strftime("%Y-%m-%d")
            if today.month == 12:
                m_end = today.replace(year=today.year+1, month=1, day=1).strftime("%Y-%m-%d")
            else:
                m_end = today.replace(month=today.month+1, day=1).strftime("%Y-%m-%d")
            m_stats = self.get_period_stats(m_start, m_end)
            report["monthly"] = {**m_stats, "limit": 120.0, "status": "VYSOKÉ NASADENIE" if m_stats["hodiny"] > 100.0 else "VYVÁŽENÉ"}

            q_num = (today.month - 1) // 3 + 1
            q_start_month = 3 * (q_num - 1) + 1
            q_start = today.replace(month=q_start_month, day=1).strftime("%Y-%m-%d")
            q_stats = self.get_period_stats(q_start, today.strftime("%Y-%m-%d"))
            report["quarterly"] = {**q_stats, "q": f"Q{q_num} {today.year}", "evaluácia": "Priebežná supervízna rovnováha a diverzifikácia partnerov."}

            h_start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
            h_stats = self.get_period_stats(h_start, today.strftime("%Y-%m-%d"))
            report["half_year"] = {**h_stats, "evaluácia": "Povinný polročný reštart a audit. Odporúča sa 14-dňový útlm a čerpanie Home Office."}

            y_start = f"{today.year}-01-01"
            y_end = f"{today.year}-12-31"
            y_stats = self.get_period_stats(y_start, y_end)
            report["yearly"] = {**y_stats, "rok": today.year, "strategia": "Konsolidácia pozície lídra v SR a ČR."}

        except Exception as e:
            report["error"] = str(e)
        return report

    def scan_anomalies(self) -> list:
        anomalies = []
        try:
            conn = get_connection()
            missing = pd.read_sql("""
                SELECT d.id, d.miesto, d.datum_akcie, d.celkova_suma, d.mena 
                FROM dopyty d
                LEFT JOIN vnutorne_faktury f ON d.id = f.dopyt_id
                WHERE (d.stav LIKE '%SCHVÁLENÉ%' OR d.stav LIKE '%SCHVALENE%') AND f.id IS NULL
            """, conn)
            for _, r in missing.iterrows():
                anomalies.append({
                    "typ": "CHÝBAJÚCA FAKTURÁCIA",
                    "popis": f"Výjazd #{r['id']} ({r['miesto'] or 'Klient'}) zo dňa {r['datum_akcie']} je schválený, ale chýba fakturačný podklad!"
                })
            conn.close()
        except Exception:
            pass
        return anomalies

    def predict_needs(self) -> list:
        predictions = []
        try:
            conn = get_connection()
            df_hist = pd.read_sql("""
                SELECT miesto, MAX(datum_akcie) as pos, AVG(hodiny) as h, AVG(celkova_suma) as s, mena
                FROM dopyty WHERE miesto IS NOT NULL AND miesto != '' GROUP BY miesto
            """, conn)
            today = datetime.now().date()
            for _, row in df_hist.iterrows():
                if row['pos']:
                    try:
                        d_diff = (today - datetime.strptime(str(row['pos'])[:10], "%Y-%m-%d").date()).days
                        if d_diff >= 25:
                            predictions.append({
                                "partner": row['miesto'],
                                "dni": d_diff,
                                "hodiny": round(row['h'] or 6.0, 1),
                                "vynos": round(row['s'] or 300.0, 2),
                                "mena": row['mena'] or "EUR"
                            })
                    except Exception:
                        pass
            conn.close()
        except Exception:
            pass
        return predictions


# Inicializácia neurosystému
neuro = EtienNeurosytemConductor()
neuro_fixes = neuro.self_heal_and_optimize()
psych_report = neuro.comprehensive_psychohygiene_audit()
anomalies = neuro.scan_anomalies()
predictions = neuro.predict_needs()
watchdog = neuro.validator.audit_systemovej_plynulosti()

# ==========================================
# NEURONÁLNY BOČNÝ PANEL
# ==========================================
st.sidebar.markdown("## 🧠 ETIENs NEUROSÝSTÉM")
st.sidebar.caption("Samoučiaci & Samoopravovací Dirigent")
st.sidebar.markdown("---")

# 🏠 TLAČIDLO DOMOV (Rýchly návrat na Veliteľský mostík)
if st.sidebar.button("🏠 Domov (Veliteľský mostík)", use_container_width=True, type="primary"):
    st.rerun()

st.sidebar.markdown("---")

if neuro_fixes["invoices_fixed"] > 0:
    st.sidebar.success(f"🧬 Neuro-Sync: Opravených {neuro_fixes['invoices_fixed']} relácií.")
elif watchdog["system_healthy"] and not anomalies:
    st.sidebar.success("🟢 Neuro-Stav: 100% Homeostáza")
else:
    st.sidebar.warning(f"🟠 Anomálie: {len(anomalies)} na vyriešenie")

w_status = psych_report.get("weekly", {})
if w_status.get("status") == "PRETÍŽENIE":
    st.sidebar.error(f"🚨 Psychohygiena (Týždeň): {w_status.get('hodiny')}h / 32h!")
else:
    st.sidebar.info(f"🧘 Týždenná záťaž: {w_status.get('hodiny', 0)}h / 32h")

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Neuronálna navigácia:",
    [
        "⚡ Veliteľský mostík (Dashboard)",
        "🧬 Štatistický & Psychohygienický Radar",
        "📥 Sondár (Inteligentný záchyt)",
        "🚗 Dispečer (Trasy & SR/ČR)",
        "💶 Financmajster (Ekonomika)"
    ]
)

st.sidebar.markdown("---")
if st.sidebar.button("⚡ Vynútiť neuro-samooopravu systému", use_container_width=True):
    res = neuro.self_heal_and_optimize()
    st.sidebar.success(f"Autonómny repozitár prečistený. Opravené: {res['invoices_fixed']}")
    st.rerun()

if not MODULY_OK:
    st.error(f"Kritická chyba modulov: {IMPORT_ERROR_MSG}")
    st.stop()

# ==========================================
# HLAVNÝ OBSAH PODĽA VÝBERU
# ==========================================
if "Veliteľský mostík" in menu:
    st.markdown("""
        <div class="neuro-banner">
            <h1 style="color: #ffffff !important; margin: 0; font-size: 2.3rem;">🧠 ETIENs Neurosystém – Veliteľský Mostík</h1>
            <p style="color: #93c5fd !important; margin-top: 0.5rem; font-size: 1.1rem;">
                Autonómny, samoučiaci a samoopravovací mozog praxe. Integrovaná legislatíva 2026, predikcie a viacúrovňové štatistiky (Piatok/Pondelok Home Office).
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Rýchly príkaz pre neuro-dirigenta
    with st.container():
        st.markdown("### 💬 Neuro-Command (Priamy hlas / text príkaz)")
        with st.form("neuro_cmd"):
            c1, c2 = st.columns([4, 1])
            with c1:
                cmd_txt = st.text_input("Zadaj požiadavku v prirodzenom jazyku (napr. Supervízia Trenčín 6 hodín, 40km):", placeholder="Napr. Krízová intervencia Praha 5 hodín...")
            with c2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                submitted_nc = st.form_submit_button("Spracovať Dirigentom", use_container_width=True)
            
            if submitted_nc and cmd_txt:
                try:
                    kraj = "ČR" if any(x in cmd_txt.lower() for x in ["praha", "brno", "ostrava", "kč"]) else "SR"
                    mena = "CZK" if kraj == "ČR" else "EUR"
                    h_val = 6.0
                    for word in cmd_txt.split():
                        if word.replace('.', '', 1).isdigit():
                            h_val = float(word)
                            break
                    
                    nid = vloz_dopyt({
                        "datum_vytvorenia": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "sluzby": "Odborná supervízia / Intervencia",
                        "hodiny": h_val,
                        "miesto": cmd_txt,
                        "krajina": kraj,
                        "datum_akcie": datetime.now().strftime("%Y-%m-%d"),
                        "stav": "VYJEDNÁVANIE",
                        "mena": mena,
                        "celkova_suma": h_val * (50.0 if kraj == "SR" else 1250.0),
                        "poznamka": f"Vytvorené cez Neuro-Command: {cmd_txt}"
                    })
                    st.success(f"🧬 Neurosystém úspešne spracoval a eviduje dopyt pod ID #{nid}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Chyba neuro-parsovania: {e}")

    st.markdown("---")

    try:
        conn = get_connection()
        cnt_d = pd.read_sql("SELECT COUNT(*) as c FROM dopyty", conn).iloc[0]['c']
        cnt_f = pd.read_sql("SELECT COUNT(*) as c FROM vnutorne_faktury", conn).iloc[0]['c']
        s_eur = pd.read_sql("SELECT SUM(suma_celkom) as s FROM vnutorne_faktury WHERE mena='EUR'", conn).iloc[0]['s'] or 0.0
        s_czk = pd.read_sql("SELECT SUM(suma_celkom) as s FROM vnutorne_faktury WHERE mena='CZK'", conn).iloc[0]['s'] or 0.0
        conn.close()
    except Exception:
        cnt_d = cnt_f = 0
        s_eur = s_czk = 0.0

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Aktívne spisy", cnt_d)
    mc2.metric("Účtovné protokoly", cnt_f)
    mc3.metric("Obrat SR", f"{s_eur:,.2f} €")
    mc4.metric("Obrat ČR", f"{s_czk:,.2f} Kč")

    st.markdown("---")

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("🚨 Akčný radar & Samooprava")
        if not anomalies:
            st.success("✅ Neurosystém neeviduje žiadne anomálie. Všetky výjazdy sú zosynchronizované.")
        else:
            for item in anomalies:
                st.markdown(f"""
                    <div class="alert-card">
                        <strong>[{item['typ']}]</strong><br/>
                        {item['popis']}
                    </div>
                """, unsafe_allow_html=True)
            if st.button("🛠️ Spustiť autonómnu opravu dier", type="primary", use_container_width=True):
                r_fix = neuro.self_heal_and_optimize()
                st.success(f"Neuro-sync úspešný! Opravených relácií: {r_fix['invoices_fixed']}")
                st.rerun()

    with col_r:
        st.subheader("🔮 Prediktívny radar (Učiaca sa pamäť)")
        if not predictions:
            st.info("Neurosystém priebežne analyzuje cykly partnerov pre budúce výjazdy.")
        else:
            for p in predictions:
                st.markdown(f"""
                    <div class="prediction-card">
                        <strong>🏢 {p['partner']}</strong><br/>
                        Posledný kontakt pred: <b>{p['dni']} dňami</b><br/>
                        Odhad rozvrhu: <b>{p['hodiny']} hod.</b> | Predikovaný výnos: <b>{p['vynos']} {p['mena']}</b>
                    </div>
                """, unsafe_allow_html=True)

elif "Štatistický & Psychohygienický Radar" in menu:
    st.markdown("""
        <div class="neuro-banner">
            <h1 style="color: #ffffff !important; margin: 0; font-size: 2.1rem;">🧬 Štatistický & Psychohygienický Radar</h1>
            <p style="color: #93c5fd !important; margin-top: 0.4rem; font-size: 1.05rem;">
                Kompletný prehľad: Odpracované hodiny, počet služieb, výnosy (SR/ČR) a najazdené kilometre v cykloch (Týždenne, Mesačne, Štvrťročne, Polročne, Ročne).
            </p>
        </div>
    """, unsafe_allow_html=True)

    w = psych_report.get("weekly", {})
    m = psych_report.get("monthly", {})
    q = psych_report.get("quarterly", {})
    h = psych_report.get("half_year", {})
    y = psych_report.get("yearly", {})

    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        # TÝŽDENNÝ PREHĽAD
        st.markdown(f"""
            <div class="neuro-card">
                <h3>📅 Týždenný prehľad (Najbližších 7 dní)</h3>
                <p><b>Odpracované hodiny:</b> {w.get('hodiny', 0):,.1f} h (Limit: {w.get('limit', 32)}h)</p>
                <p><b>Stav vyťaženia:</b> <span style="color: {'#ef4444' if w.get('status')=='PRETÍŽENIE' else '#22c55e'};"><b>{w.get('status', 'OK')}</b></span></p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <p><b>Počet služieb / akcií:</b> {w.get('sluzby', 0)}</p>
                <p><b>Výnosy SR:</b> {w.get('eur', 0):,.2f} € | <b>Výnosy ČR:</b> {w.get('czk', 0):,.2f} Kč</p>
                <p><b>Najazdené kilometre:</b> {w.get('km', 0):,.1f} km</p>
                <p style="font-size: 0.82rem; color: #94a3b8; margin-top: 0.4rem;"><i>Piatok a Pondelok vyhradené pre Home Office.</i></p>
            </div>
        """, unsafe_allow_html=True)

        # MESAČNÝ PREHĽAD
        st.markdown(f"""
            <div class="neuro-card">
                <h3>📊 Mesačný prehľad (Aktuálny mesiac)</h3>
                <p><b>Odpracované hodiny:</b> {m.get('hodiny', 0):,.1f} h (Limit: {m.get('limit', 120)}h)</p>
                <p><b>Biorytmus:</b> {m.get('status', 'Vyvážené')}</p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <p><b>Počet služieb / akcií:</b> {m.get('sluzby', 0)}</p>
                <p><b>Výnosy SR:</b> {m.get('eur', 0):,.2f} € | <b>Výnosy ČR:</b> {m.get('czk', 0):,.2f} Kč</p>
                <p><b>Najazdené kilometre:</b> {m.get('km', 0):,.1f} km</p>
            </div>
        """, unsafe_allow_html=True)

    with col_w2:
        # ŠTVRŤROČNÝ PREHĽAD
        st.markdown(f"""
            <div class="neuro-card">
                <h3>📈 Štvrťročný prehľad ({q.get('q', 'Q')})</h3>
                <p>{q.get('evaluácia', '')}</p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <p><b>Celkom hodín:</b> {q.get('hodiny', 0):,.1f} h | <b>Akcií:</b> {q.get('sluzby', 0)}</p>
                <p><b>Výnosy SR:</b> {q.get('eur', 0):,.2f} € | <b>Výnosy ČR:</b> {q.get('czk', 0):,.2f} Kč</p>
                <p><b>Najazdené kilometre:</b> {q.get('km', 0):,.1f} km</p>
            </div>
        """, unsafe_allow_html=True)

        # POLROČNÝ PREHĽAD
        st.markdown(f"""
            <div class="neuro-card">
                <h3>⏳ Polročný audit (Posledných 6 mesiacov)</h3>
                <p>{h.get('evaluácia', '')}</p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <p><b>Celkom hodín:</b> {h.get('hodiny', 0):,.1f} h | <b>Akcií:</b> {h.get('sluzby', 0)}</p>
                <p><b>Výnosy SR:</b> {h.get('eur', 0):,.2f} € | <b>Výnosy ČR:</b> {h.get('czk', 0):,.2f} Kč</p>
                <p><b>Najazdené kilometre:</b> {h.get('km', 0):,.1f} km</p>
            </div>
        """, unsafe_allow_html=True)

    # ROČNÝ PREHĽAD (Široký banner dole)
    st.markdown(f"""
        <div class="neuro-card" style="background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%); border: 1px solid #38bdf8;">
            <h3>🎯 Ročná makro-syntéza ({y.get('rok', 2026)})</h3>
            <p><b>Strategický smer:</b> {y.get('strategia', '')}</p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
                <div><b>Celkovo hodín:</b> {y.get('hodiny', 0):,.1f} h</div>
                <div><b>Celkovo služieb:</b> {y.get('sluzby', 0)}</div>
                <div><b>Obrat SR:</b> {y.get('eur', 0):,.2f} €</div>
                <div><b>Obrat ČR:</b> {y.get('czk', 0):,.2f} Kč</div>
                <div><b>Najazdené km:</b> {y.get('km', 0):,.1f} km</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

elif "Sondár" in menu:
    dopyty_modul.render()
elif "Dispečer" in menu:
    vyjazd_modul.render()
elif "Financmajster" in menu:
    fakturacia_modul.render()
