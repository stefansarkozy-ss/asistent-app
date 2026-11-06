# ==========================================
# database.py - CENTRÁLNA SQLITE DATABÁZA
# ==========================================

import os
import sqlite3
import pandas as pd

DB_NAME = "asistent.db"


def get_connection():
  return sqlite3.connect(DB_NAME)


def init_db():
  """Inicializuje všetky potrebné tabuľky v centrálnej databáze."""
  conn = get_connection()
  cursor = conn.cursor()

  # Tabuľka dopytov / výjazdov
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS dopyty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum_vytvorenia TEXT,
            sluzby TEXT,
            hodiny REAL,
            miesto TEXT,
            krajina TEXT,
            datum_akcie TEXT,
            cas TEXT,
            ubytovanie REAL,
            strava REAL,
            km INTEGER,
            stav TEXT,
            poznamka TEXT,
            mena TEXT,
            celkova_suma REAL,
            navrh_odpovedi TEXT
        )
    """)

  # Tabuľka vnútorných faktúr / výkazov
  cursor.execute("""
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
    """)

  # Tabuľka iDoklad partnerov
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS partneri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazov TEXT,
            ico TEXT,
            dic TEXT,
            adresa TEXT,
            krajina TEXT
        )
    """)

  conn.commit()
  conn.close()


def importuj_partnerov_z_csv():
  """Automaticky načíta partnerov z iDoklad CSV exportov, ak existujú."""
  conn = get_connection()
  cursor = conn.cursor()

  for subor, krajina in [("partneri_sr.csv", "SR"), ("partneri_cz.csv", "ČR")]:
    if os.path.exists(subor):
      try:
        df = pd.read_csv(subor)
        for _, row in df.iterrows():
          nazov = row.get("Název", row.get("Nazov", ""))
          ico = str(row.get("IČO", row.get("ICO", "")))
          dic = str(row.get("DIČ", row.get("DIC", "")))
          adresa = (
              f"{row.get('Ulice', '')}, {row.get('Město', row.get('Mesto', ''))}"
          )
          if nazov:
            cursor.execute(
                """
                        INSERT OR IGNORE INTO partneri (nazov, ico, dic, adresa, krajina)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                (nazov, ico, dic, adresa, krajina),
            )
      except Exception as e:
        print(f"Chyba pri importe {subor}: {e}")

  conn.commit()
  conn.close()


if __name__ == "__main__":
  init_db()
  importuj_partnerov_z_csv()