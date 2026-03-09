import streamlit as st
from supabase import create_client
from fpdf import FPDF
import requests
import io
from PIL import Image
import os

# Connexion Supabase
URL = "https://xqclkymzecsyhoubtszz.supabase.co"
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

def clean_txt(text):
    """Nettoie le texte pour PDF"""
    if not text: return ""
    replacements = {'°': '°', '²': '^2', '×': 'x', '™': '', '®': '', 'µ': 'u', 'Ω': 'Ohm'}
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    return text.encode('latin-1', 'replace').decode('latin-1')

class TechPDF(FPDF):
    def header(self):
        self.set_fill_color(0, 71, 155)
        self.rect(0, 0, 210, 8, 'F')

def get_product_image(prod_ref):
    """Récupère image produit (simulé - à adapter avec ton API images)"""
    # Exemple avec tes images ou recherche
    image_urls = {
        "C11CJ68501": "https://example.com/ecotank-l3250.jpg",  # Remplace par vraie URL
        "9S6-3BA91F-031": "https://pplx-res.cloudinary.com/image/upload/pplx_search_images/e3d962a8c33979989405a9e5f7b06d0dd47bfe30.jpg"
    }
    return image_urls.get(prod_ref.upper(), None)

def generate_pro_pdf(prod_name, brand, ref, specs, price=None):
    pdf = TechPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False, margin=15)

    cat_id = specs.get("GeneralInfo", {}).get("Category", {}).get("ID", 0)

    # Configuration par catégorie
    if cat_id in [303, 712]:  # IMPRESSION
        cfg = {"n": "IMPRESSION", "c": (0, 51, 153), "l": ["VITESSE", "WIFI", "RESOLUTION", "TYPE"]}
    elif cat_id in [160, 202, 1584]:  # ECRANS / TV
        cfg = {"n": "AFFICHAGE", "c": (20, 90, 50), "l": ["TAILLE", "RESOLUTION", "HERTZ", "DALLE"]}
    elif cat_id in [151, 189]:  # PC
        cfg = {"n": "INFORMATIQUE", "c": (44, 62, 80), "l": ["CPU", "RAM", "STOCKAGE", "ECRAN"]}
    else:
        cfg = {"n": "HARDWARE", "c": (80, 80, 80), "l": ["MARQUE", "PN", "TYPE", "USAGE"]}

    # === HEADER ===
    pdf.set_xy(10, 12)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*cfg["c"])
    pdf.cell(0, 10, clean_txt(prod_name), ln=1, align='C')

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(60, 60, 60)
    subtitle = f"{brand} | PN: {ref} | {cfg['n']}"
    if price:
        subtitle += f" | {price}"
    pdf.cell(0, 8, clean_txt(subtitle), ln=1, align='C')

    # Image produit
    image_url = get_product_image(ref)
    if image_url:
        try:
            response = requests.get(image_url, timeout=5)
            img = Image.open(io.BytesIO(response.content))
            img_path = f"/tmp/{ref}.jpg"
            img.save(img_path)
            pdf.image(img_path, x=150, y=15, w=45)
            os.remove(img_path)  # Cleanup
        except:
            pdf.set_xy(150, 20)
            pdf.set_font("Helvetica", "", 12)
            pdf.cell(0, 10, "🖼️", ln=1)

    pdf.ln(5)

    # === BLOC CARACTÉRISTIQUES CLÉS (2 colonnes) ===
    pdf.set_xy(10, 45)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*cfg["c"])
    pdf.cell(95, 7, "🔑 CARACTÉRISTIQUES CLÉS", ln=1)

    pdf.set_fill_color(248, 249, 250)
    pdf.set_draw_color(*cfg["c"])
    pdf.rect(10, 52, 95, 45, 'D')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    
    key_features = []
    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"][:2]:  # 2 premiers groupes
            for feat in group.get("Features", [])[:4]:  # 4 features max
                n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                v = feat.get("PresentationValue", "")
                if n and v:
                    key_features.append(f"• {n}: {v}")
    
    pdf.set_xy(15, 57)
    pdf.multi_cell(90, 5, "\n".join(key_features[:8]))

    # Bloc Dimensions (droite)
    pdf.set_xy(115, 45)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*cfg["c"])
    pdf.cell(85, 7, "📏 DIMENSIONS & POIDS", ln=1)

    pdf.set_fill_color(248, 249, 250)
    pdf.set_draw_color(*cfg["c"])
    pdf.rect(115, 52, 85, 45, 'D')

    pdf.set_xy(120, 57)
    pdf.set_font("Helvetica", "", 10)
    
    g_info = specs.get("GeneralInfo", {})
    dims = g_info.get("Dimensions", {})
    dim_text = []
    if dims.get("Width"):
        dim_text.append(f"LxPxH: {dims['Width']} x {dims.get('Depth','')} x {dims.get('Height','')}")
    if g_info.get("Weight"):
        dim_text.append(f"Poids: {g_info['Weight']}")
    pdf.multi_cell(80, 5, "\n".join(dim_text) or "Non spécifié")

    # === TABLEAU SPÉCIFICATIONS ===
    y_table_start = 105
    pdf.set_xy(10, y_table_start)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*cfg["c"])
    pdf.cell(190, 8, "⚙️ SPÉCIFICATIONS TECHNIQUES", ln=1, align='C')

    # En-têtes tableau
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(90, 6, "Caractéristique", 1, 0, 'L')
    pdf.cell(100, 6, "Valeur", 1, 1, 'L')

    pdf.set_font("Helvetica", "", 9)
    row_count = 0

    if "FeaturesGroups" in specs:
        for group in specs["FeaturesGroups"]:
            # Titre de groupe
            gname = group.get("GroupName", "")
            if gname:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_fill_color(230, 240, 255)
                pdf.cell(190, 5, clean_txt(gname), 1, 1, 'L')
                pdf.set_font("Helvetica", "", 9)

            for feat in group.get("Features", []):
                n = feat.get("Feature", {}).get("Name", {}).get("Value", "")
                v = feat.get("PresentationValue", "")
                
                if n and v:
                    # Saut de page si nécessaire
                    if pdf.get_y() > 270:
                        pdf.add_page()
                        pdf.set_font("Helvetica", "B", 10)
                        pdf.cell(90, 6, "Caractéristique", 1, 0, 'L', 1)
                        pdf.cell(100, 6, "Valeur", 1, 1, 'L')
                        pdf.set_font("Helvetica", "", 9)

                    pdf.cell(90, 5, clean_txt(n), 1)
                    pdf.multi_cell(100, 5, clean_txt(v), 1)
                    row_count += 1

    # === FOOTER ===
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Généré par WIKIDATA IT | {brand} {ref} | Electroplanet Maroc | 09/03/2026", 0, 1, 'C')

    return bytes(pdf.output(dest="S"))

# === INTERFACE STREAMLIT ===
st.set_page_config(page_title="WIKIDATA IT", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <h1 style='text-align: center; color: #00479b;'>🌐 <strong>WIKIDATA IT</strong></h1>
    <p style='text-align: center; color: #666;'>Générateur de fiches techniques professionnelles</p>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("🔍 Référence Constructeur (PN)", placeholder="Ex: C11CJ68501 ou 9S6-3BA91F-031", key="pn_input")
with col2:
    st.write("##")
    btn_search = st.button("🚀 GÉNÉRER FICHE PDF", use_container_width=True, type="primary")

if btn_search and query:
    q_upper = query.strip().upper()
    with st.spinner("Recherche en base..."):
        res = supabase.table("it_specs_maroc").select("*").eq("ref_constructeur", q_upper).execute()
    
    if res.data:
        prod = res.data[0]
        specs = prod.get('specs_json', {})
        
        st.success(f"✅ **{prod['nom_produit']}** trouvé !")
        
        # Aperçu rapide
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("🛒 Marque", prod['marque'])
        with col_b:
            st.metric("📋 PN", prod['ref_constructeur'])
        with col_c:
            price = prod.get('prix_public', 'NC')
            st.metric("💰 Prix", price)

        # Aperçu specs
        if "FeaturesGroups" in specs:
            with st.expander("📋 Détails techniques complets", expanded=False):
                for i, group in enumerate(specs["FeaturesGroups"]):
                    with st.container():
                        st.markdown(f"**{group.get('GroupName', f'Groupe {i+1}')}**")
                        data = []
                        for feat in group.get("Features", []):
                            n = feat.get("Feature", {}).get("Name", {}).get("Value")
                            v = feat.get("PresentationValue")
                            if n and v:
                                data.append({"**Caractéristique**": n, "**Valeur**": v})
                        st.dataframe(data, hide_index=True, use_container_width=True)

        # Génération PDF
        with st.spinner("🎨 Génération fiche professionnelle..."):
            pdf_bytes = generate_pro_pdf(
                prod['nom_produit'],
                prod['marque'],
                prod['ref_constructeur'],
                specs,
                price=prod.get('prix_public')
            )
        
        st.balloons()
        st.download_button(
            "📥 **TÉLÉCHARGER FICHE PDF**",
            pdf_bytes,
            f"WIKIDATA_{q_upper}.pdf",
            "application/pdf",
            use_container_width=True
        )
        
        st.info("✅ **Fiche générée au format datasheet professionnelle** (A4, 1 page)")
        
    else:
        # Log besoin client
        supabase.table("besoin_client").insert({
            "reference_cherchee": q_upper,
            "date": "2026-03-09"
        }).execute()
        
        st.error("❌ PN non trouvé. **Besoin enregistré** pour indexation future.")
        st.info("Essaie: `C11CJ68501` (EcoTank) ou `9S6-3BA91F-031` (MSI écran)")

# Sidebar aide
with st.sidebar:
    st.markdown("### 📖 Guide d'utilisation")
    st.write("""
    1. **Saisis un PN** (ex: C11CJ68501)
    2. **Clique GÉNÉRER**
    3. **Télécharge ta fiche PDF pro**
    
    **Formats supportés :**
    - 🖨️ Impression (cat 303/712)
    - 🖥️ Écrans/TV (cat 160/202)
    - 💻 PC (cat 151/189)
    - ⚙️ Hardware générique
    """)
    
    if st.button("🆘 Test avec EcoTank L3250"):
        st.session_state['pn_input'] = "C11CJ68501"
