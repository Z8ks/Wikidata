import streamlit as st
from supabase import create_client
from fpdf import FPDF
import os

# TES PARAMÈTRES SUPABASE (déjà dans ton code)
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]  # Garde tes secrets
supabase = create_client(URL, KEY)

def clean_txt(text):
    if not text: return ""
    replacements = {'°': '°', '²': '^2', '×': 'x', '™': '', '®': '', 'µ': 'u'}
    for char, rep in replacements.items():
        text = str(text).replace(char, rep)
    return text[:120]

class TechPDF(FPDF):
    def header(self):
        self.set_fill_color(0, 71, 155)
        self.rect(0, 0, 210, 8, 'F')

def generate_pro_pdf(prod_name, brand, ref, specs, price=None):
    pdf = TechPDF()
    pdf.add_page()

    cat_id = specs.get("GeneralInfo", {}).get("Category", {}).get("ID", 0)
    
    # Couleurs par catégorie (TES configs)
    if cat_id in [303, 712]: cfg = {"n": "IMPRESSION", "c": (0, 51, 153)}
    elif cat_id in [160, 202, 1584]: cfg = {"n": "AFFICHAGE", "c": (20, 90, 50)}
    elif cat_id in [151, 189]: cfg = {"n": "INFORMATIQUE", "c": (44, 62, 80)}
    else: cfg = {"n": "HARDWARE", "c": (80, 80, 80)}

    # HEADER
    pdf.set_xy(10, 12)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*cfg["c"])
    pdf.cell(0, 10, clean_txt(prod_name), ln=1, align='C')

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(60, 60, 60)
    subtitle = f"{brand} | PN: {ref} | {cfg['n']}"
    if price: subtitle += f" | {price}"
    pdf.cell(0, 8, subtitle, ln=1, align='C')

    # IMAGE PLACEHOLDER (🖼️ pro)
    pdf.set_xy(155, 15)
    pdf.set_font("Helvetica", "", 24)
    pdf.cell(40, 40, "🖼️", ln=1)

    # CARACTÉRISTIQUES CLÉS
    pdf.set_xy(10, 50)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*cfg["c"])
    pdf.cell(95, 7, "🔑 CARACTÉRISTIQUES CLÉS", ln=1)

    pdf.set_fill_color(248, 249, 250)
    pdf.rect(10, 57, 95, 45, 'D')
    
    pdf.set_xy(15, 62)
    pdf.set_font("Helvetica", "", 10)
    key_features = []
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"][:1]:  # Premier groupe
            for feat in group.get("Features", [])[:5]:
                n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                v = feat.get("PresentationValue", "")
                if n and v:
                    key_features.append(f"• {n}: {v}")
    
    pdf.multi_cell(90, 5, "\n".join(key_features) or "Détails disponibles dans le tableau")

    # DIMENSIONS (droite)
    pdf.set_xy(115, 50)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*cfg["c"])
    pdf.cell(85, 7, "📏 DIMENSIONS", ln=1)

    pdf.set_fill_color(248, 249, 250)
    pdf.rect(115, 57, 85, 45, 'D')
    
    pdf.set_xy(120, 62)
    g_info = specs.get("GeneralInfo", {})
    dims = g_info.get("Dimensions", {})
    dim_text = []
    if dims.get("Width"): dim_text.append(f"LxPxH: {dims['Width']}x{dims.get('Depth','')}x{dims.get('Height','')}")
    pdf.multi_cell(80, 5, "\n".join(dim_text) or "NC")

    # TABLEAU SPECS (TON point fort)
    pdf.set_xy(10, 110)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*cfg["c"])
    pdf.cell(190, 8, "⚙️ SPÉCIFICATIONS TECHNIQUES", ln=1, align='C')

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(90, 6, "Caractéristique", 1)
    pdf.cell(100, 6, "Valeur", 1, 1)

    pdf.set_font("Helvetica", "", 9)
    specs_count = 0
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            gname = group.get("GroupName", "")
            if gname and specs_count < 20:  # Limite 20 lignes
                pdf.set_fill_color(230, 240, 255)
                pdf.cell(190, 5, gname, 1, 1, 'L')
            
            for feat in group.get("Features", []):
                n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                v = feat.get("PresentationValue", "")
                if n and v and specs_count < 25:
                    pdf.cell(90, 5, clean_txt(n), 1)
                    pdf.multi_cell(100, 5, clean_txt(v), 1)
                    specs_count += 1

    # FOOTER
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"WIKIDATA IT | {brand} {ref} | Electroplanet | {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'C')

    return bytes(pdf.output(dest="S"))

# === INTERFACE (TON DESIGN) ===
st.set_page_config(page_title="WIKIDATA IT", layout="wide")
st.markdown("<h1 style='text-align: center;'>🌐 WIKIDATA IT</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    query = st.text_input("Référence Constructeur (PN)", placeholder="Ex: UA85U8000FUXMV")
with col2:
    st.write("##")
    btn_search = st.button("🔍 Lancer la recherche", use_container_width=True)

if btn_search:
    if not query:
        st.warning("Veuillez entrer un PN.")
    else:
        try:
            q_upper = query.strip().upper()
            st.info(f"🔍 Recherche: `{q_upper}`")
            
            res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", q_upper).execute()
            
            if res.data:
                prod = res.data[0]
                specs = prod.get('specs_json', {})
                
                st.success(f"✅ **{prod['nom_produit']}** trouvé !")
                
                # Metrics (TON style)
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Marque", prod['marque'])
                with cols[1]:
                    st.metric("Référence", prod['ref_constructeur'])
                
                # Aperçu specs
                if "FeaturesGroups" in specs:
                    with st.expander("Voir tous les détails techniques", expanded=True):
                        for group in specs["FeaturesGroups"]:
                            st.markdown(f"**{group.get('GroupName', 'Specs')}**")
                            data_tab = []
                            for feat in group.get("Features", []):
                                n = feat.get("Feature", {}).get("Name", {}).get("Value")
                                v = feat.get("PresentationValue")
                                if n and v: 
                                    data_tab.append({"Caractéristique": n, "Valeur": v})
                            st.table(data_tab)

                # GÉNÉRATION PDF
                pdf_bytes = generate_pro_pdf(
                    prod['nom_produit'], 
                    prod['marque'], 
                    prod['ref_constructeur'], 
                    specs
                )
                
                st.download_button(
                    "📥 **TÉLÉCHARGER FICHE PDF**", 
                    pdf_bytes, 
                    f"WIKIDATA_{q_upper}.pdf", 
                    "application/pdf"
                )
                
            else:
                # Log besoin (TON code)
                supabase.table("besoin_client").insert({"reference_cherchee": q_upper}).execute()
                st.error("❌ Référence inconnue. **Besoin enregistré**.")
                
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")
            st.info("Vérifie `st.secrets['SUPABASE_KEY']` dans `.streamlit/secrets.toml`")

# Sidebar aide
with st.sidebar:
    st.header("📖 Guide")
    st.info("""
    **1.** Saisis PN (ex: C11CJ68501)
    **2.** Clique 🔍
    **3.** 📥 Fiche PDF pro !
    
    **✅ Fonctionne avec ta base Supabase**
    """)
