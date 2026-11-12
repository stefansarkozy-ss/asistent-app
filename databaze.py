# ==========================================
# databaze.py - Centrálna SQLite databáza (ETIENs Neurosystém)
# ==========================================

from __future__ import annotations

import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "asistent.db")

NOVE_STLPCE_DOPYTOV = {
    "message_id": "TEXT",
    "thread_subject": "TEXT",
    "odosielatel": "TEXT",
    "predmet": "TEXT",
    "text": "TEXT",
    "org": "TEXT",
    "meno": "TEXT",
    "email": "TEXT",
    "telefon": "TEXT",
    "adresa": "TEXT",
    "popis": "TEXT",
    "zdrojovy_text": "TEXT",
    "hodiny_zdroj": "TEXT",
    "km_tam": "REAL",
    "spatocna": "INTEGER DEFAULT 1",
    "spotreba": "REAL",
    "palivo": "TEXT",
    "gcal_url": "TEXT",
    "gcal_event_id": "TEXT",
    "chybajuce_udaje": "TEXT",
    "naklady_json": "TEXT",
}

POVOLENE_POLIA = {
    "datum_vytvorenia",
    "sluzby",
    "hodiny",
    "miesto",
    "krajina",
    "datum_akcie",
    "cas",
    "cestovny_cas",
    "odchod",
    "cena_sluzby",
    "cena_cestovne",
    "ubytovanie",
    "strava",
    "km",
    "stav",
    "poznamka",
    "mena",
    "celkova_suma",
    *NOVE_STLPCE_DOPYTOV.keys(),
}


def get_connection() -> sqlite3.Connection:
    """Vráti pripojenie do SQLite databázy."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _existujuce_stlpce(conn: sqlite3.Connection, tabulka: str) -> set[str]:
    return {riadok[1] for riadok in conn.execute(f"PRAGMA table_info({tabulka})")}


def _dopln_stlpce(conn: sqlite3.Connection, tabulka: str, stlpce: dict[str, str]) -> None:
    existujuce = _existujuce_stlpce(conn, tabulka)
    for nazov, typ in stlpce.items():
        if nazov not in existujuce:
            conn.execute(f"ALTER TABLE {tabulka} ADD COLUMN {nazov} {typ}")


def init_db() -> None:
    """Inicializuje všetky potrebné tabuľky a automaticky doplní chýbajúce stĺpce."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS dopyty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            thread_subject TEXT,
            datum_vytvorenia TEXT,
            odosielatel TEXT,
            predmet TEXT,
            text TEXT,
            org TEXT,
            sluzby TEXT,
            hodiny REAL,
            miesto TEXT,
            krajina TEXT,
            datum_akcie TEXT,
            cas TEXT,
            cestovny_cas REAL,
            odchod TEXT,
            cena_sluzby REAL,
            cena_cestovne REAL,
            ubytovanie REAL,
            strava REAL,
            km INTEGER,
            stav TEXT DEFAULT 'ROZPRACOVANÉ',
            poznamka TEXT,
            mena TEXT DEFAULT '€',
            celkova_suma REAL DEFAULT 0.0
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vnutorne_faktury (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dopyt_id INTEGER,
            datum_generovania TEXT,
            entita TEXT,
            odberatel TEXT,
            popis_sluzieb TEXT,
            suma_celkom REAL,
            mena TEXT,
            stav_podkladu TEXT,
            json_payload TEXT
        )
        """
    )
    cursor.execute(
        """
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
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sondar_history (
            message_id TEXT PRIMARY KEY,
            sender TEXT,
            timestamp TEXT,
            status TEXT,
            dopyt_id INTEGER
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_kroky (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dopyt_id INTEGER,
            cas TEXT,
            agent TEXT,
            sprava TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_alias_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            klucove_slovo TEXT UNIQUE,
            partner_nazov TEXT,
            typ_sluzby TEXT,
            avg_hodiny REAL,
            krajina TEXT
        )
        """
    )
    _dopln_stlpce(conn, "dopyty", NOVE_STLPCE_DOPYTOV)
    _dopln_stlpce(conn, "sondar_history", {"dopyt_id": "INTEGER"})
    _dopln_stlpce(
        conn,
        "ai_alias_map",
        {"pocet_interakcii": "INTEGER DEFAULT 1", "posledna_interakcia": "TEXT"},
    )
    conn.commit()
    conn.close()
    importuj_partnerov_z_csv()


def init_all_tables() -> None:
    """Alias pre spätnú kompatibilitu (vyžadovaný v app.py)."""
    init_db()


def importuj_partnerov_z_csv() -> None:
    try:
        import pandas as pd
    except ImportError:
        return

    conn = get_connection()
    cursor = conn.cursor()
    for subor, krajina in (("partneri_sr.csv", "SR"), ("partneri_cz.csv", "ČR")):
        cesta = os.path.join(BASE_DIR, subor)
        if not os.path.exists(cesta) or os.path.getsize(cesta) < 10:
            continue
        try:
            df = pd.read_csv(cesta)
        except Exception:
            continue
        for _, row in df.iterrows():
            nazov = _csv_bunka(row, "Nazov", "Název", "Názov", "Firma")
            if not nazov:
                continue
            uz_je = cursor.execute(
                "SELECT 1 FROM partneri WHERE nazov = ? AND krajina = ?",
                (nazov, krajina),
            ).fetchone()
            if uz_je:
                continue
            adresa = _csv_bunka(row, "Adresa")
            if not adresa:
                ulica = _csv_bunka(row, "Ulice", "Ulica")
                mesto = _csv_bunka(row, "Město", "Mesto")
                adresa = ", ".join(cast for cast in (ulica, mesto) if cast)
            cursor.execute(
                """
                INSERT INTO partneri (ico, dic, nazov, adresa, krajina, zdroj, datum_pridania)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _csv_bunka(row, "ICO", "IČO"),
                    _csv_bunka(row, "DIC", "DIČ"),
                    nazov,
                    adresa,
                    krajina,
                    subor,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
    conn.commit()
    conn.close()


def _csv_bunka(row, *nazvy: str) -> str:
    indexy = {str(k).lower(): k for k in row.index}
    for nazov in nazvy:
        kluc = indexy.get(nazov.lower())
        if kluc is None:
            continue
        hodnota = row[kluc]
        if hodnota is None or (isinstance(hodnota, float) and hodnota != hodnota):
            continue
        text = str(hodnota).strip()
        if text and text.lower() != "nan":
            return text
    return ""


def pridaj_krok(dopyt_id: int, agent: str, sprava: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO agent_kroky (dopyt_id, cas, agent, sprava) VALUES (?, ?, ?, ?)",
        (dopyt_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), agent, sprava),
    )
    conn.commit()
    conn.close()


def kroky_dopytu(dopyt_id: int) -> list[dict]:
    conn = get_connection()
    riadky = conn.execute(
        "SELECT * FROM agent_kroky WHERE dopyt_id = ? ORDER BY id",
        (dopyt_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in riadky]


def posledne_kroky(limit: int = 12) -> list[dict]:
    conn = get_connection()
    riadky = conn.execute(
        "SELECT * FROM agent_kroky ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in riadky]


def vloz_dopyt(*args, **kwargs) -> int:
    """
    Univerzálne vloženie dopytu:
    Podporuje volanie cez slovník vloz_dopyt({'org': ...}) 
    aj priame volanie s 10 parametrami vloz_dopyt(message_id, thread_subject, ...).
    """
    if len(args) == 1 and isinstance(args[0], dict):
        polia = args[0]
    elif len(args) >= 10:
        polia = {
            "message_id": args[0],
            "thread_subject": args[1],
            "datum_vytvorenia": args[2],
            "odosielatel": args[3],
            "predmet": args[4],
            "text": args[5],
            "stav": args[6],
            "org": args[7],
            "miesto": args[8],
            "celkova_suma": args[9],
        }
    else:
        polia = kwargs

    ciste = {k: v for k, v in polia.items() if k in POVOLENE_POLIA}
    stlpce = ", ".join(ciste.keys())
    zastupky = ", ".join("?" for _ in ciste)
    conn = get_connection()
    cursor = conn.execute(
        f"INSERT OR IGNORE INTO dopyty ({stlpce}) VALUES ({zastupky})",
        tuple(ciste.values()),
    )
    dopyt_id = int(cursor.lastrowid or 0)
    conn.commit()
    conn.close()
    return dopyt_id


def aktualizuj_dopyt(dopyt_id: int, polia: dict) -> None:
    ciste = {k: v for k, v in polia.items() if k in POVOLENE_POLIA}
    if not ciste:
        return
    priradenie = ", ".join(f"{k} = ?" for k in ciste)
    conn = get_connection()
    conn.execute(
        f"UPDATE dopyty SET {priradenie} WHERE id = ?",
        (*ciste.values(), dopyt_id),
    )
    conn.commit()
    conn.close()


def nacitaj_dopyt(dopyt_id: int) -> dict | None:
    conn = get_connection()
    riadok = conn.execute("SELECT * FROM dopyty WHERE id = ?", (dopyt_id,)).fetchone()
    conn.close()
    return dict(riadok) if riadok else None


def vsetky_dopyty() -> list[dict]:
    conn = get_connection()
    riadky = conn.execute("SELECT * FROM dopyty ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in riadky]


def zapamataj_partnera(organizacia: str, sluzba: str, hodiny: float, krajina: str) -> None:
    if not organizacia:
        return
    kluc = organizacia.strip().lower()[:80]
    conn = get_connection()
    teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    existujuci = conn.execute(
        "SELECT id, avg_hodiny, pocet_interakcii FROM ai_alias_map WHERE klucove_slovo = ?",
        (kluc,),
    ).fetchone()
    if existujuci and "pocet_interakcii" in existujuci.keys() and existujuci["pocet_interakcii"]:
        pocet = int(existujuci["pocet_interakcii"]) + 1
        priemer = round(((float(existujuci["avg_hodiny"] or 0) * (pocet - 1)) + hodiny) / pocet, 2)
        conn.execute(
            """
            UPDATE ai_alias_map
            SET partner_nazov = ?, typ_sluzby = ?, avg_hodiny = ?, krajina = ?,
                pocet_interakcii = ?, posledna_interakcia = ?
            WHERE id = ?
            """,
            (organizacia, sluzba, priemer, krajina, pocet, teraz, existujuci["id"]),
        )
    elif existujuci:
        conn.execute(
            """
            UPDATE ai_alias_map
            SET partner_nazov = ?, typ_sluzby = ?, avg_hodiny = ?, krajina = ?,
                pocet_interakcii = 1, posledna_interakcia = ?
            WHERE id = ?
            """,
            (organizacia, sluzba, hodiny, krajina, teraz, existujuci["id"]),
        )
    else:
        conn.execute(
            """
            INSERT INTO ai_alias_map (
                klucove_slovo, partner_nazov, typ_sluzby, avg_hodiny, krajina,
                pocet_interakcii, posledna_interakcia
            ) VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (kluc, organizacia, sluzba, hodiny, krajina, teraz),
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
