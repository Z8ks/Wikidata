import io
from typing import Any, Dict, List

import streamlit as st
from supabase import create_client
from fpdf import FPDF

# -----------------------------
# 1. CONFIG & SUPABASE CLIENT
# -----------------------------

SUPABASE_URL = "https://xqclkymzecsyhoubtszz.supabase.co"
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Palette de couleurs
PRIMARY = (0, 51, 153)
ACCENT = (255, 102, 0)
LIGHT_BG = (245, 247, 250)
TEXT_MAIN = (40, 40, 40)
TEXT_MUTED = (110, 110, 110)
GREY_LIGHT = (220, 220, 220)

# -----------------------------
# 2. UTILITAIRES MÉTIER (inchangés)
# -----------------------------

def normalize_specs(raw_specs: Dict[str, Any]) -> Dict[str, Any]:
    features_groups = raw_specs.get("FeaturesGroups", [])
    normalized_groups = []
    for group in features_groups:
        name = group.get("GroupName", "")
        features = []
        for feat in group.get("Features", []):
            n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
            v = feat.get("PresentationValue", "")
            if n and v:
                features.append({"name": n, "value": v})
        if features:
            normalized_groups.append({"name": name, "features": features})

    general_info = raw_specs.get("GeneralInfo", {})
    image_url = (
        general_info.get("Image", {}).get("HighPic")
        or general_info.get("Image", {}).get("LowPic")
    )

    return {
        "image_url": image_url,
        "groups": normalized_groups,
    }

def compute_badges(normalized_specs: Dict[str, Any], prod_name: str) -> List[Dict[str, Any]]:
    full_text = (prod_name + " " + str(normalized_specs)).lower()
    badges: List[Dict[str, Any]] = []
    
    if "wifi" in full_text or "802.11" in full_text:
        badges.append({"label": "Wi-Fi", "color": PRIMARY})
    if "tank" in full_text or "bouteille" in full_text or "ecotank" in full_text:
        badges.append({"label": "Eco-Tank", "color": ACCENT})
    if "usb" in full_text:
        badges.append({"label": "Connectivité USB", "color": PRIMARY})
    if "a4" in full_text or "a4 format" in full_text:
        badges.append({"label": "Format A4", "color": PRIMARY})
    
    if not badges:
        badges.append({"label": "Fiabilité Pro", "color": PRIMARY})
    
    return badges[:4]

def get_brand_logo_url(brand: str, fallback_url: str | None = None) -> str | None:
    brand = (brand or "").strip()
    if not brand:
        return fallback_url
    brand_domain = f"{brand.lower().replace(' ', '')}.com"
    return f"https://logo.clearbit.com/{brand_domain}"

# -----------------------------
# 3. CLASSE PDF (inchangée)
# -----------------------------

class PremiumBrochure(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_left_margin(10)
        self.set_right_margin(10)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, "WIKIDATA IT - L'expertise Hardware au Maroc", align="C")

    def set_title_style(self):
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*PRIMARY)

    def set_subtitle_style(self):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*TEXT_MUTED)

    def set_section_title_style(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*PRIMARY)

    def set_body_text_style(self):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*TEXT_MAIN)

# -----------------------------
# 4. RENDU PDF (inchangé)
# -----------------------------

def draw_header(pdf: PremiumBrochure, brand: str, prod_name: str, ref: str, logo_url: str | None):
    pdf.add_page()
    pdf.set_fill_color(*LIGHT_BG)
    pdf.rect(0, 0, pdf.w, 40, "F")

    if logo_url:
        try:
            pdf.image(logo_url, x=10, y=8, w=25)
        except Exception:
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(*PRIMARY)
            pdf.text(12, 22, brand.upper())
    else:
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*PRIMARY)
        pdf.text(12, 22, brand.upper())

    pdf.set_xy(40, 10)
    pdf.set_title_style()
    pdf.multi_cell(150, 8, prod_name.upper())
    pdf.set_xy(40, 28)
    pdf.set_subtitle_style()
    pdf.cell(0, 6, f"Référence constructeur : {ref}")

def draw_badges(pdf: PremiumBrochure, badges: List[Dict[str, Any]]):
    if not badges:
        return
    pdf.set_y(45)
    pdf.set_x(10)
    for badge in badges:
        label = badge["label"]
        color = badge["color"]
        pdf.set_fill_color(*color)
        pdf.set_text_color(255, 255, 255)
        curr_x = pdf.get_x()
        curr_y = pdf.get_y()
        padding_x = 2
        padding_y = 1.5
        pdf.set_font("Helvetica", "B", 8)
        text_width = pdf.get_string_width(label) + padding_x * 2
        height = 7
        pdf.rect(curr_x, curr_y, text_width, height, "F")
        pdf.set_xy(curr_x + padding_x, curr_y + padding_y)
        pdf.cell(text_width - padding_x * 2, 4, label, align="C")
        pdf.set_xy(curr_x + text_width + 3, curr_y)

def draw_body(pdf: PremiumBrochure, normalized_specs: Dict[str, Any]):
    y_start = 60
    pdf.set_y(y_start)
    image_url = normalized_specs.get("image_url")
    if image_url:
        try:
            pdf.image(image_url, x=10, y=y_start, w=70)
        except Exception:
            pass
    x_right = 85
    w_col = pdf.w - x_right - 10
    pdf.set_xy(x_right, y_start)
    pdf.set_body_text_style()
    for group in normalized_specs.get("groups", []):
        g_name = (group.get("name") or "").upper()
        if g_name in ["GÉNÉRAL", "GENERAL", "SPECS", "INFO"]:
            continue
        pdf.set_x(x_right)
        pdf.set_section_title_style()
        pdf.set_fill_color(*LIGHT_BG)
        pdf.cell(w_col, 7, f"  {g_name}", ln=True, fill=True)
        pdf.ln(1)
        pdf.set_body_text_style()
        for feat in group.get("features", []):
            n = feat["name"]
            v = feat["value"]
            line = f"> {n}: {v}"
            safe_line = line.encode("latin-1", "replace").decode("latin-1")
            pdf.set_x(x_right + 2)
            pdf.multi_cell(w_col - 4, 3.8, safe_line)
        pdf.ln(3)
        if pdf.get_y() > (pdf.h - 25):
            break

# ✅ CORRECTION CLÉ ICI
def generate_pdf(prod_name: str, brand: str, ref: str, specs: Dict[str, Any]) -> bytes:
    normalized_specs = normalize_specs(specs)
    badges = compute_badges(normalized_specs, prod_name)
    logo_url = get_brand_logo_url(brand)

    pdf = PremiumBrochure(orientation="P", unit="mm", format="A4")

    draw_header(pdf, brand=brand, prod_name=prod_name, ref=ref, logo_url=logo_url)
    draw_badges(pdf, badges)
    draw_body(pdf, normalized_specs)

    # ✅ CORRECTION DÉFINITIVE : bytearray → bytes
    pdf_output = pdf.output(dest="S")
    if isinstance(pdf_output, bytearray):
        pdf_bytes = bytes(pdf_output)  # Conversion explicite
    else:
        pdf_bytes = pdf_output
    
    return pdf_bytes
# -----------------------------
# 5. INTERFACE STREAMLIT (inchangée)
# -----------------------------

st.markdown(
    "<h1 style='text-align: center; color: #003399;'>🌐 WIKIDATA IT</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #555;'>Génération de brochures techniques premium à partir de vos références constructeurs.</p>",
    unsafe_allow_html=True,
)

query = st.text_input("Référence constructeur (PN)", placeholder="C11CJ67408")

if query:
    with st.spinner("Recherche de la fiche technique dans WIKIDATA IT..."):
        res = (
            supabase.table("it_specs_maroc")
            .select("*")
            .eq("ref_constructeur", query.strip())
            .limit(1)
            .execute()
        )

    if res.data:
        prod = res.data[0]
        st.info(
            f"Produit trouvé : **{prod.get('nom_produit', 'Nom inconnu')}** – Marque : {prod.get('marque', 'N/A')}"
        )

        if st.button("Générer la brochure premium (PDF)"):
            try:
                pdf_bytes = generate_pdf(
                    prod_name=prod["nom_produit"],
                    brand=prod["marque"],
                    ref=prod["ref_constructeur"],
                    specs=prod["specs_json"],
                )

                st.download_button(
                    label="📥 Télécharger la brochure premium (PDF)",
                    data=pdf_bytes,
                    file_name=f"WIKIDATA_{query.strip()}.pdf",
                    mime="application/pdf",
                    type="primary",
                )
                st.success("Brochure générée avec succès.")
            except Exception as e:
                st.error(f"Erreur lors de la génération du PDF : {e}")
    else:
        st.warning("Aucun produit trouvé pour cette référence.")

