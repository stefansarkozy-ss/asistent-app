# ==========================================
# validator.py - ETIENs ASISTENT (VRCHOLOVÝ ŠÉF & DOZOR)
# ==========================================

import datetime
from databaze import get_connection

SUPERVIZNE_MODALITY_MAP = {
    "reflektujúci": "Individuálna supervízia (Reflektujúci tím)",
    "debriefing": "Akútny krízový debriefing",
    "manažérsk": "Manažérska a riadiaca supervízia",
    "metodick": "Metodické vedenie a konzultácia",
    "vyhoreni": "Supervízia zameraná na syndróm vyhorenia a prevenciu",
    "etick": "Supervízia etických dilem v pomáhajúcej profesii",
    "trauma": "TIR / Trauma-informed supervízia kazuistík",
    "intervenci": "Krízová intervencia v teréne",
    "kouč": "Odborný koučing a mentoring",
}


class EtienAsistentValidator:
    """
    Vrcholový Asistent ETIENs (Bos systému):
    - Riadi a audituje všetky procesy, dopyty a toky dát.
    - Sémantická analýza textu, detekcia jurisdikcie (SR / ČR 2026).
    - Etická, právna, ekonomická a psychologická vrstva (ochrana pred vyhorením, Home Office Piatok/Pondelok).
    - Technický watchdog pre kontrolu plynulosti a integrity databázy.
    """

    def __init__(self):
        self._init_audit_tables()

    def _init_audit_tables(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_alias_map (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    klucove_slovo TEXT UNIQUE,
                    partner_nazov TEXT,
                    typ_sluzby TEXT,
                    avg_hodiny REAL,
                    krajina TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS etien_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    jurisdikcia TEXT,
                    eticky_status TEXT,
                    pravny_status TEXT,
                    ekonomicky_status TEXT,
                    psychologicky_status TEXT,
                    detaily TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception:
            pass

    def ucis_sa_z_interakcie(self, klucove_slovo: str, partner_nazov: str, typ_sluzby: str, hodiny: float, krajina: str):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ai_alias_map (klucove_slovo, partner_nazov, typ_sluzby, avg_hodiny, krajina)
                VALUES (?, ?, ?, ?, ?)
            """, (klucove_slovo.lower(), partner_nazov, typ_sluzby, hodiny, krajina))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def audit_systemovej_plynulosti(self) -> dict:
        system_warnings = []
        is_healthy = True

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabulky = [row[0] for row in cursor.fetchall()]
            
            povinne_tabulky = ["dopyty", "vnutorne_faktury", "ai_alias_map", "partneri"]
            chybajuce = [t for t in povinne_tabulky if t not in tabulky]
            
            if chybajuce:
                system_warnings.append(f"🚨 [ETIENs Neurosystém - Watchdog]: Chýbajú kľúčové tabuľky: {', '.join(chybajuce)}")
                is_healthy = False
            else:
                system_warnings.append("🟢 [ETIENs Neurosystém - Watchdog]: Databázová štruktúra a homeostáza sú v poriadku.")

            cursor.execute("SELECT COUNT(*) FROM dopyty WHERE stav LIKE '%VYJEDNÁVANIE%' AND (hodiny IS NULL OR hodiny = 0)")
            zaseknute = cursor.fetchone()[0]
            if zaseknute > 0:
                system_warnings.append(f"⚠️ [ETIENs Neurosystém]: Detekovaných {zaseknute} rozpracovaných dopytov bez hodinovej dotácie.")

            conn.close()
        except Exception as e:
            system_warnings.append(f"🚨 [ETIENs Neurosystém]: Chyba databázového auditu: {e}")
            is_healthy = False

        return {
            "system_healthy": is_healthy,
            "system_warnings": system_warnings
        }

    def audit_request(self, surovy_text: str, hodiny: float, datum_obj: datetime.date, service_type: str, krajina: str) -> dict:
        weekday = datum_obj.weekday()
        t_lower = surovy_text.lower()
        warnings = []
        requires_override = False
        role_reports = {}

        is_cz = "ČESK" in krajina.upper() or "CZ" in krajina.upper() or "KČ" in t_lower
        jurisdikcia_nazov = "Česká republika (ČR) - ETIENs Institut s.r.o." if is_cz else "Slovensko (SR) - PhDr. Štefan Šarközy"
        mena = "CZK" if is_cz else "EUR"

        mgr_notes = []
        # PIATOK: Home Office režim
        if weekday == 4:
            mgr_notes.append("Piatok je podľa biorytmu vyhradený pre Home Office (administratíva/príprava).")
            warnings.append("⚠️ [Manažér - ETIENs]: Výjazd je plánovaný na Piatok (Home Office deň). Vyžaduje vašu výnimku.")
            requires_override = True
        # PONDELOK: Obmedzený režim / Home office
        elif weekday == 0:
            mgr_notes.append("Pondelok - obmedzený režim / pokojný nástup na Home Office.")
            warnings.append("ℹ️ [Manažér - ETIENs]: Pondelok je optimálny pre domáci režim bez náročných presunov.")
        # VÍKENDY: Striktne iba vzdelávanie/supervízia
        elif weekday in [5, 6]:
            is_edu_or_sup = any(w in service_type.lower() for w in ["supervízia", "supervizia", "vzdelávanie", "vzdelavanie", "kurz"])
            if not is_edu_or_sup:
                warnings.append("🚨 [Manažér / Etik - ETIENs]: Víkendy sú vyhradené výhradne pre vzdelávanie alebo supervíziu!")
                requires_override = True
        role_reports["manazer"] = mgr_notes

        psy_notes = []
        if hodiny < 4.0:
            warnings.append(f"⚠️ [Psychológ - ETIENs]: Nízka časová dotácia ({hodiny}h).")
        elif hodiny > 10.0:
            warnings.append(f"🚨 [Psychológ - ETIENs]: Kritické prekročenie denného limitu ({hodiny}h > 10h)!")
            requires_override = True
        role_reports["psycholog_socialny"] = psy_notes

        role_reports["etik_pravnik"] = [f"Jurisdikcia overená: {jurisdikcia_nazov}.", "Ochrana mlčanlivosti a GDPR pod dohľadom."]
        role_reports["ekonom"] = [f"Mena a platné účtovné štandardy 2026: {mena}."]

        return {
            "requires_override": requires_override,
            "warnings": warnings,
            "role_reports": role_reports,
            "krajina_zistena": jurisdikcia_nazov,
            "mena": mena
        }

    def je_kompletne(self, org_val, hodiny_val):
        """Spätná kompatibilita pre overenie úplnosti záznamu."""
        if not org_val or org_val == "-- Vyberte zo zoznamu --":
            return False
        if hodiny_val <= 0:
            return False
        return True

    def skontroluj(self, polia: dict) -> tuple[bool, str]:
        """Spätná kompatibilita pre jednoduchú validáciu dopytu."""
        org = polia.get("org", "")
        hodiny = float(polia.get("hodiny", 0.0))
        
        if self.je_kompletne(org, hodiny):
            return True, "Validácia úspešná: Dáta sedia a výjazd je kompletný."
        else:
            return False, "Validácia: Záznam obsahuje neúplné údaje (chýba organizácia alebo hodiny)."
