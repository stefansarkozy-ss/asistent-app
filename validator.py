# ==========================================
# validator.py - NEUROPLASTICKÝ AI MOZOG & KAZUISTICKÝ ENGINE
# ==========================================

import datetime
import json
import re
import urllib.parse
from databaze import get_connection

SUPERVIZNE_MODALITY_MAP = {
    "reflektujúci": "Individuálna supervízia (Reflektujúci tím)",
    "debriefing": "Akútny krízový debriefing",
    "manažérsk": "Manažérska a riadiaca supervízia",
    "metodick": "Metodické vedenie a konzultácia",
    "vyhoreni": "Supervízia zameraná na syndróm vyhorenia a prevenciu",
    "etick": "Supervízia etických dilem v pomáhajúcej profesii",
    "trauma": "TIR / Trauma-informed supervízia kazuistík",
}

KM_DB = {
    "jelka": 90,
    "cífer": 100,
    "piešťany": 160,
    "príbeta": 220,
    "šaľa": 130,
    "dss javorinská": 20,
    "pezinok": 50,
    "partizánske": 290,
    "trnava": 90,
    "nitra": 180,
    "brno": 260,
    "praha": 660,
    "bystřice nad pernštejnem": 220,
    "zlobice": 190,
    "orlová": 340,
    "trenčín": 240,
    "žilina": 400,
}

MIESTA_CR = [
    "brno",
    "praha",
    "bystřice nad pernštejnem",
    "zlobice",
    "orlová",
    "etien",
    "česká republika",
    "čr",
    "kč",
    "korún",
]
MIESTA_SR = [
    "jelka",
    "cífer",
    "piešťany",
    "príbeta",
    "šaľa",
    "dss javorinská",
    "pezinok",
    "partizánske",
    "trnava",
    "nitra",
    "bratislava",
    "trenčín",
    "žilina",
    "slovensko",
    "sr",
    "eur",
    "eurách",
]


def init_neuro_tables():
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
  conn.commit()
  conn.close()


def ucis_sa_z_interakcie(klucove_slovo, partner_nazov, typ_sluzby, hodiny, krajina):
  init_neuro_tables()
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT OR REPLACE INTO ai_alias_map (klucove_slovo, partner_nazov, typ_sluzby, avg_hodiny, krajina)
        VALUES (?, ?, ?, ?, ?)
    """,
      (klucove_slovo.lower(), partner_nazov, typ_sluzby, hodiny, krajina),
  )
  conn.commit()
  conn.close()


def vyhladaj_v_adaptivnej_pamati(t_lower):
  init_neuro_tables()
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT klucove_slovo, partner_nazov, typ_sluzby, avg_hodiny, krajina FROM"
      " ai_alias_map"
  )
  zaznamy = cursor.fetchall()
  conn.close()

  for kluc, partner, sluzba, hodiny, krajina in zaznamy:
    if kluc in t_lower:
      return {
          "partner": partner,
          "sluzba": sluzba,
          "hodiny": hodiny if hodiny else 4.0,
          "krajina": krajina,
      }
  return None


def parse_hodiny_z_textu(t_lower):
  hodiny_match = re.search(r"(\d+[\.,]?\d*)\s*(hod|h|hodin)", t_lower)
  if hodiny_match:
    return float(hodiny_match.group(1).replace(",", "."))

  if "pol dňa" in t_lower or "celý deň" in t_lower:
    return 6.0
  if "poldruha" in t_lower or "hodinu a pol" in t_lower:
    return 1.5
  if "dve hodiny" in t_lower or "2 hodiny" in t_lower:
    return 2.0
  if "tri hodiny" in t_lower or "3 hodiny" in t_lower:
    return 3.0
  if "štyri hodiny" in t_lower or "4 hodiny" in t_lower:
    return 4.0
  if "päť hodín" in t_lower or "5 hodín" in t_lower:
    return 5.0
  if "šesť hodín" in t_lower or "6 hodín" in t_lower:
    return 6.0

  return 0.0


def najdi_partnera_v_idoklade(miesto_text):
  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT nazov, ico, dic, adresa FROM partneri ORDER BY nazov ASC"
  )
  partneri = cursor.fetchall()
  conn.close()

  m_lower = miesto_text.lower()
  for nazov, ico, dic, adresa in partneri:
    if any(s in nazov.lower() for s in m_lower.split() if len(s) > 3):
      return {
          "nazov": nazov,
          "ico": ico if ico else "Nezadané",
          "dic": dic if dic else "",
          "adresa": adresa,
      }

  return {
      "nazov": miesto_text,
      "ico": "Nezadané",
      "dic": "",
      "adresa": miesto_text,
  }


def vygeneruj_gcal_url(title, date_str, time_str, duration_hours, location, details):
  try:
    start_dt = datetime.datetime.strptime(
        f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
    )
  except Exception:
    start_dt = datetime.datetime.now()
  end_dt = start_dt + datetime.timedelta(hours=duration_hours)

  fmt = "%Y%m%dT%H%M%S"
  params = {
      "action": "TEMPLATE",
      "text": title,
      "dates": f"{start_dt.strftime(fmt)}Z/{end_dt.strftime(fmt)}Z",
      "details": details,
      "location": location,
  }
  return (
      "https://calendar.google.com/calendar/render?"
      f"{urllib.parse.urlencode(params)}"
  )


def spracuj_vstup_koordinatorom(surovy_text, entita_hint="Slovensko (SR)"):
  t_lower = surovy_text.lower()

  zistené_modality = []
  kazuisticky_typ_sluzby = None
  for kluc, modalita in SUPERVIZNE_MODALITY_MAP.items():
    if kluc in t_lower:
      zistené_modality.append(modalita)
      if not kazuisticky_typ_sluzby and "supervíz" in modalita.lower():
        kazuisticky_typ_sluzby = modalita

  adaptivna_zhoda = vyhladaj_v_adaptivnej_pamati(t_lower)

  hodiny = parse_hodiny_z_textu(t_lower)
  if hodiny == 0.0 and adaptivna_zhoda:
    hodiny = adaptivna_zhoda["hodiny"]

  if adaptivna_zhoda:
    krajina = adaptivna_zhoda["krajina"]
    mena = "CZK" if "Česká" in krajina else "EUR"
  else:
    if any(kw in t_lower for kw in MIESTA_CR):
      krajina = "Česká republika (ČR) - Etien Institut s.r.o."
      mena = "CZK"
    else:
      krajina = "Slovensko (SR) - PhDr. Štefan Šarközy"
      mena = "EUR"

  if kazuisticky_typ_sluzby:
    sluzba_typ = kazuisticky_typ_sluzby
  elif adaptivna_zhoda:
    sluzba_typ = adaptivna_zhoda["sluzba"]
  else:
    sluzba_typ = "SI - individuálna supervízia"
    if "skupinov" in t_lower:
      sluzba_typ = "SS - skupinová supervízia"
    elif "krízov" in t_lower or "intervenci" in t_lower:
      sluzba_typ = "KI - krízová intervencia"
    elif "kouč" in t_lower:
      sluzba_typ = "K - koučing"
    elif "vzdelávan" in t_lower or "školen" in t_lower:
      sluzba_typ = "V - vzdelávanie"

  if adaptivna_zhoda:
    miesto = adaptivna_zhoda["partner"]
  else:
    miesto = "Neznáme miesto"
    for m in KM_DB.keys():
      if m in t_lower:
        miesto = m.title()
        break

  is_complete = (miesto != "Neznáme miesto") and (hodiny > 0)

  conn = get_connection()
  cursor = conn.cursor()
  dnes_str = datetime.date.today().strftime("%Y-%m-%d")

  if not is_complete:
    navrh_odpovedi = (
        f"Dobrý deň, zaznamenal som dopyt na '{surovy_text}'. Prosím doplňte"
        " mi chýbajúce údaje (presné miesto a počet hodín)."
    )
    cursor.execute(
        """
            INSERT INTO dopyty (datum_vytvorenia, sluzby, hodiny, miesto, krajina, datum_akcie, cas, ubytovanie, strava, km, stav, poznamka, mena, celkova_suma, navrh_odpovedi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            sluzba_typ,
            hodiny,
            surovy_text,
            krajina,
            dnes_str,
            "09:00",
            0.0,
            0.0,
            0,
            "Čaká na doplnenie",
            surovy_text,
            mena,
            0.0,
            navrh_odpovedi,
        ),
    )
    d_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"status": "Caka", "id": d_id, "navrh_odpovedi": navrh_odpovedi}
  else:
    klucove_slovo_z_textu = next(
        (w for w in t_lower.split() if len(w) > 3), miesto.lower()
    )
    ucis_sa_z_interakcie(
        klucove_slovo_z_textu, miesto, sluzba_typ, hodiny, krajina
    )

    km = KM_DB.get(miesto.lower(), 50)
    sadzba_hodina = 50.0
    sadzba_km = 0.55 if "česká" in krajina.lower() else 0.52

    suma_sluzby = hodiny * sadzba_hodina
    cena_cestovne = km * sadzba_km
    celkova_suma = suma_sluzby + cena_cestovne

    partner = najdi_partnera_v_idoklade(miesto)

    zapisana_poznamka = surovy_text
    if zistené_modality:
      zapisana_poznamka += (
          f" | Zistené modality: {', '.join(zistené_modality)}"
      )

    cursor.execute(
        """
            INSERT INTO dopyty (datum_vytvorenia, sluzby, hodiny, miesto, krajina, datum_akcie, cas, ubytovanie, strava, km, stav, poznamka, mena, celkova_suma)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            sluzba_typ,
            hodiny,
            partner["nazov"],
            krajina,
            dnes_str,
            "09:00",
            0.0,
            0.0,
            km,
            "Schválené",
            zapisana_poznamka,
            mena,
            celkova_suma,
        ),
    )
    d_id = cursor.lastrowid

    json_payload = json.dumps(
        {
            "OdberatelNazov": partner["nazov"],
            "OdberatelICO": partner["ico"],
            "OdberatelDIC": partner["dic"],
            "OdberatelMiesto": partner["adresa"],
            "DatumAkcie": dnes_str,
            "CasAkcie": "09:00",
            "SumaZaSluzby": suma_sluzby,
            "CenaCestovne": cena_cestovne,
            "Kilometre": km,
            "Ubytovanie": 0.0,
            "Strava": 0.0,
            "Krajina": krajina,
            "Poznamka": zapisana_poznamka,
            "KazuistickeModality": zistené_modality,
        },
        ensure_ascii=False,
    )

    popis_sluzieb = f"• {sluzba_typ}: {hodiny} hod. x {sadzba_hodina} {mena}/h = {suma_sluzby} {mena}"

    cursor.execute(
        """
            INSERT OR REPLACE INTO vnutorne_faktury (dopyt_id, datum_generovania, entita, odberatel, popis_sluzieb, suma_celkom, mena, stav_podkladu, json_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            d_id,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            krajina,
            partner["nazov"],
            popis_sluzieb,
            celkova_suma,
            mena,
            "Schválené",
            json_payload,
        ),
    )

    conn.commit()
    conn.close()

    gcal_url = vygeneruj_gcal_url(
        f"{sluzba_typ} ({partner['nazov']})",
        dnes_str,
        "09:00",
        hodiny,
        partner["adresa"],
        f"Suma: {celkova_suma} {mena}",
    )

    return {
        "status": "Schválené",
        "id": d_id,
        "miesto": partner["nazov"],
        "sluzby": sluzba_typ,
        "hodiny": hodiny,
        "celkova_suma": celkova_suma,
        "mena": mena,
        "gcal_url": gcal_url,
    }