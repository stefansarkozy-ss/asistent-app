# ==========================================
# modules/fakturacia_modul.py - VYLEPŠENÝ WORD EXPORT
# ==========================================

import io
import json
import pandas as pd
import streamlit as st
from database import get_connection

try:
  from docx import Document
  from docx.enum.table import WD_TABLE_ALIGNMENT
  from docx.enum.text import WD_ALIGN_PARAGRAPH
  from docx.oxml import parse_xml
  from docx.oxml.ns import nsdecls
  from docx.shared import Inches, Pt, RGBColor

  DOCX_AVAILABLE = True
except ImportError:
  DOCX_AVAILABLE = False


def set_cell_background(cell, hex_color):
  tcPr = cell._tc.get_or_add_tcPr()
  shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
  tcPr.append(shd)


def generovat_word_protokol(json_data):
  doc = Document()
  for section in doc.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

  mena = "CZK" if "Česká" in json_data.get("Krajina", "") else "EUR"
  entita_nazov = (
      "Etien Institut s.r.o. (ČR)"
      if mena == "CZK"
      else "PhDr. Štefan Šarközy (SR)"
  )

  p_title = doc.add_paragraph()
  run_title = p_title.add_run("VÝKAZ ODBORNEJ ČINNOSTI A CESTOVNÝCH NÁHRAD")
  run_title.font.name = "Arial"
  run_title.font.size = Pt(15)
  run_title.font.bold = True
  run_title.font.color.rgb = RGBColor(30, 58, 138)
  p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

  p_sub = doc.add_paragraph()
  run_sub = p_sub.add_run(f"Podklad pre internú fakturáciu / {entita_nazov}")
  run_sub.font.name = "Arial"
  run_sub.font.size = Pt(10)
  run_sub.font.italic = True
  run_sub.font.color.rgb = RGBColor(100, 116, 139)
  p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

  doc.add_paragraph()

  box_table = doc.add_table(rows=1, cols=2)
  box_table.alignment = WD_TABLE_ALIGNMENT.CENTER
  box_table.autofit = False
  cells = box_table.rows[0].cells
  cells[0].width = Inches(3.3)
  cells[1].width = Inches(3.3)

  p_dod = cells[0].paragraphs[0]
  p_dod.add_run("DODÁVATEĽ:\n").bold = True
  p_dod.add_run(f"{json_data.get('Krajina', 'PhDr. Štefan Šarközy')}\n")
  p_dod.add_run(f"Dátum výjazdu: {json_data.get('DatumAkcie', '')}\n")

  p_odb = cells[1].paragraphs[0]
  p_odb.add_run("ODBERATEĽ / MIESTO:\n").bold = True
  p_odb.add_run(f"{json_data.get('OdberatelNazov', '')}\n")
  p_odb.add_run(f"Adresa: {json_data.get('OdberatelMiesto', '')}\n")
  ico = json_data.get("OdberatelICO", "Nezadané")
  if ico and ico != "Nezadané":
    p_odb.add_run(f"IČO: {ico}\n")

  set_cell_background(cells[0], "F8FAFC")
  set_cell_background(cells[1], "F8FAFC")

  doc.add_paragraph()

  table = doc.add_table(rows=1, cols=4)
  table.alignment = WD_TABLE_ALIGNMENT.CENTER
  table.autofit = False
  col_widths = [Inches(3.2), Inches(1.1), Inches(1.1), Inches(1.2)]
  hdr_cells = table.rows[0].cells
  headers = [
      "Popis položky / Služby",
      "Rozsah / Km",
      "Sadzba",
      f"Spolu ({mena})",
  ]
  for i, title in enumerate(headers):
    hdr_cells[i].width = col_widths[i]
    p = hdr_cells[i].paragraphs[0]
    r = p.add_run(title)
    r.bold = True
    r.font.color.rgb = RGBColor(255, 255, 255)
    set_cell_background(hdr_cells[i], "1E3A8A")
    if i >= 1:
      p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

  suma_sluzby = json_data.get("SumaZaSluzby", 0)
  r1 = table.add_row().cells
  r1[0].paragraphs[0].add_run("Odborná činnosť / Supervízia / Konzultácia")
  r1[1].paragraphs[0].add_run("1 úkon")
  r1[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
  r1[2].paragraphs[0].add_run("-")
  r1[3].paragraphs[0].add_run(f"{suma_sluzby:.2f}")
  r1[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

  cena_km = json_data.get("CenaCestovne", 0)
  km = json_data.get("Kilometre", 0)
  if cena_km > 0 or km > 0:
    r2 = table.add_row().cells
    r2[0].paragraphs[0].add_run("Cestovné náhrady (Automobil)")
    r2[1].paragraphs[0].add_run(f"{km} km")
    r2[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r2[2].paragraphs[0].add_run(f"{(cena_km/km):.2f}" if km > 0 else "-")
    r2[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r2[3].paragraphs[0].add_run(f"{cena_km:.2f}")
    r2[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

  doc.add_paragraph()

  celkom = suma_sluzby + cena_km
  p_sum = doc.add_paragraph()
  p_sum.alignment = WD_ALIGN_PARAGRAPH.RIGHT
  p_sum.add_run("CELKOVÁ SUMA NA ÚHRADU: ").bold = True
  r_sum_val = p_sum.add_run(f"{celkom:.2f} {mena}")
  r_sum_val.bold = True
  r_sum_val.font.size = Pt(14)
  r_sum_val.font.color.rgb = RGBColor(30, 58, 138)

  if json_data.get("Poznamka"):
    doc.add_paragraph()
    p_poz = doc.add_paragraph()
    p_poz.add_run("Poznámka / Kazuistika k výjazdu:\n").bold = True
    p_poz.add_run(json_data.get("Poznamka", ""))

  file_stream = io.BytesIO()
  doc.save(file_stream)
  file_stream.seek(0)
  return file_stream


def render():
  st.header("🧾 Vnútorná fakturácia & Word export")
  st.caption("Generovanie štruktúrovaných Word protokolov (.docx) pre SR a ČR.")

  if not DOCX_AVAILABLE:
    st.error(
        "Knižnica `python-docx` nie je nainštalovaná. Spustite `pip install"
        " python-docx`."
    )
    return

  conn = get_connection()
  df = pd.read_sql("SELECT * FROM vnutorne_faktury ORDER BY id DESC", conn)
  conn.close()

  if df.empty:
    st.info("Zatiaľ nie sú vytvorené žiadne podklady pre fakturáciu.")
  else:
    for _, row in df.iterrows():
      with st.expander(
          f"Fakturačný podklad #{row['id']} | Odberateľ: {row['odberatel']}"
          f" ({row['suma_celkom']} {row['mena']})"
      ):
        st.markdown(f"**Entita:** {row['entita']}")
        st.markdown(f"**Popis:** {row['popis_sluzieb']}")
        st.markdown(f"**Celkom:** `{row['suma_celkom']} {row['mena']}`")

        try:
          json_data = json.loads(row["json_payload"])
        except Exception:
          json_data = {}

        if st.button(
            f"📥 Pripraviť Word protokol (#{row['id']})",
            key=f"btn_docx_{row['id']}",
        ):
          docx_stream = generovat_word_protokol(json_data)
          st.download_button(
              label="💾 Stiahnuť Word súbor (.docx)",
              data=docx_stream,
              file_name=(
                  f"Protokol_Vyjazd_{row['id']}_{row['odberatel'].replace(' ', '_')}.docx"
              ),
              mime=(
                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              ),
              key=f"download_docx_{row['id']}",
          )