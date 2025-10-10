import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128

# ------------------------------
# Helper Functions
# ------------------------------

def generate_bin_codes(start_prefix, middle_values, start_aisle, end_aisle,
                       level_letters, start_level, end_level):
    """
    Generate bin codes including dash before level.
    Returns list of strings.
    """
    codes = []
    for mid in middle_values:
        for aisle in range(start_aisle, end_aisle + 1):
            if level_letters:
                for letter in level_letters:
                    for level in range(start_level, end_level + 1):
                        code = f"{start_prefix}{mid}{aisle:02}{letter}-{level}"
                        codes.append(code)
            else:
                for level in range(start_level, end_level + 1):
                    code = f"{start_prefix}{mid}{aisle:02}-{level}"
                    codes.append(code)
    return codes

def draw_labels_pdf(codes, label_w_in, label_h_in, orientation, page_size):
    """
    Draw Code128 barcoded labels into a PDF buffer.
    Barcode on top, human-readable text below.
    """
    label_w = label_w_in * inch
    label_h = label_h_in * inch
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=page_size)

    if orientation == "vertical":
        label_w, label_h = label_h, label_w

    margin_x = 0.25 * inch
    margin_y = 0.25 * inch
    x = margin_x
    y = margin_y

    for code in codes:
        c.saveState()
        try:
            # Code128 barcode
            barcode = code128.Code128(code, barHeight=1.2*inch, humanReadable=0)
            barcode_width = barcode.width
            scale = min((label_w - 0.5*inch)/barcode_width, 1.5)
            c.translate(x + (label_w - barcode_width*scale)/2.0, y + label_h - 1.7*inch)
            c.scale(scale, scale)
            barcode.drawOn(c, 0, 0)

            # Human-readable text below
            c.restoreState()
            c.setFont("Helvetica-Bold", 40)
            text_y = y + 0.7*inch
            c.drawCentredString(x + label_w/2.0, text_y, code)

            # Optional label border
            c.rect(x, y, label_w, label_h, stroke=0, fill=0)
        except Exception as e:
            st.error(f"Error drawing barcode {code}: {e}")
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

# ------------------------------
# Streamlit UI
# ------------------------------

st.title("🏷️ Warehouse Bin Label Generator (Code128)")
st.write("Generate printable warehouse bin labels with customizable sequences and layout.")

col1, col2 = st.columns(2)

with col1:
    prefix = st.text_input("Start Prefix", "16")
    middle_input = st.text_input("Middle Section(s) (comma-separated)", "EA,ED,EF")
    start_aisle = st.number_input("Start Aisle", 1, 999, 1)
    end_aisle = st.number_input("End Aisle", 1, 999, 20)

with col2:
    level_letters_input = st.text_input("Level Letter(s) (comma-separated, optional)", "A,B,C,D")
    start_level = st.number_input("Start Level", 1, 50, 1)
    end_level = st.number_input("End Level", 1, 50, 5)

st.divider()
st.subheader("📄 Label & Page Settings")
col3, col4 = st.columns(2)

with col3:
    label_w_in = st.number_input("Label Width (inches)", 1.0, 12.0, 4.0)
    label_h_in = st.number_input("Label Height (inches)", 1.0, 12.0, 6.0)
    orientation = st.selectbox("Label Orientation", ["horizontal", "vertical"], index=0)

with col4:
    page_type = st.selectbox("Page Size", ["4x6", "Letter", "A4"], index=0)

# Determine page size
if page_type == "A4":
    page_size = A4
elif page_type == "Letter":
    page_size = letter
else:
    page_size = (4*inch, 6*inch)

if st.button("🚀 Generate Labels PDF"):
    middle_values = [m.strip().upper() for m in middle_input.split(",") if m.strip()]
    level_letters = [x.strip().upper() for x in level_letters_input.split(",") if x.strip()] or None

    if not middle_values:
        st.error("Please provide at least one middle section (e.g., EA, ED, EF).")
    else:
        try:
            codes = generate_bin_codes(prefix, middle_values, start_aisle, end_aisle,
                                       level_letters, start_level, end_level)
            if not codes:
                st.warning("No labels generated. Check your inputs.")
            else:
                pdf_buffer = draw_labels_pdf(codes, label_w_in, label_h_in, orientation, page_size)
                st.success(f"✅ Generated {len(codes)} labels successfully!")
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_buffer,
                    file_name="warehouse_bin_labels.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Error generating labels: {e}")

st.caption("Barcodes now use **Code128** — fully scannable, dash included, each label fills the full 4×6 inch page by default.")
