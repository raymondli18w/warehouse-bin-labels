import streamlit as st
from fpdf import FPDF
from io import BytesIO
from barcode import Code128
from barcode.writer import ImageWriter
import re
import os

# -----------------------------
# Bypass python-barcode's overzealous validation
# -----------------------------
# Code128 supports: 0-9, A-Z, and symbols including '-', which is ASCII 45
# But python-barcode < 0.16 blocks '-' in some cases.
# Workaround: monkey-patch the validation or construct raw

# We'll use a safe method: ensure string only contains allowed Code128 chars
def is_valid_code128(s):
    # Code128 character set includes uppercase letters, digits, and many symbols
    # Hyphen '-' is allowed (ASCII 45)
    return bool(re.fullmatch(r"[A-Z0-9\-]+", s)) and len(s) > 0

# -----------------------------
st.set_page_config(page_title="Warehouse Bin Label Generator", layout="wide")
st.title("🏷️ Warehouse Bin Label Generator")

# --- Inputs ---
prefix = st.text_input("Prefix", value="16EA")
start_middle = st.text_input("Start Middle (number)", value="21")
end_middle = st.text_input("End Middle (number)", value="32")
start_level_letter = st.text_input("Start Level Letter (optional, comma-separated)", value="")
start_level = st.text_input("Start Level (optional, numeric)", value="1")
end_level_letter = st.text_input("End Level Letter (optional, comma-separated)", value="")
end_level = st.text_input("End Level (optional, numeric)", value="1")

label_width = st.number_input("Label Width (inches)", value=4.0, min_value=1.0)
label_height = st.number_input("Label Height (inches)", value=6.0, min_value=1.0)
labels_per_row = st.number_input("Labels per row", value=2, min_value=1, step=1)
labels_per_column = st.number_input("Labels per column", value=3, min_value=1, step=1)

generate_button = st.button("Generate PDF Labels")

# -----------------------------
def generate_codes():
    if not start_middle or not end_middle:
        st.error("Please enter numeric values for 'Start Middle' and 'End Middle'.")
        return []

    try:
        middle_nums = range(int(start_middle), int(end_middle) + 1)
    except ValueError:
        st.error("Start/End Middle must be integers.")
        return []

    try:
        level_nums = range(int(start_level), int(end_level) + 1) if start_level and end_level else [None]
    except ValueError:
        st.error("Level fields must be integers if provided.")
        return []

    level_letters = [s.strip().upper() for s in start_level_letter.split(",")] if start_level_letter else [None]

    codes = []
    for m in middle_nums:
        for ll in level_letters:
            for lv in level_nums:
                base = f"{prefix}{m:02d}"
                if ll:
                    base += ll
                display_code = f"{base}-{lv}" if lv is not None else base

                # Now: KEEP the hyphen for barcode
                if is_valid_code128(display_code):
                    codes.append(display_code)
                else:
                    st.warning(f"Skipped invalid code: {display_code}")
    return codes

# -----------------------------
def create_pdf(codes):
    page_width = label_width * labels_per_row
    page_height = label_height * labels_per_column
    pdf = FPDF(unit="in", format=(page_width, page_height))
    pdf.set_auto_page_break(False)

    temp_files = []

    for i, code in enumerate(codes):
        if i % (labels_per_row * labels_per_column) == 0:
            pdf.add_page()
            x_offset = 0
            y_offset = 0

        # Generate barcode WITH hyphen
        # Note: We rely on the fact that '-' is valid in Code128
        # Some versions of python-barcode allow it if the string is clean
        try:
            barcode = Code128(code, writer=ImageWriter())
        except Exception as e:
            st.error(f"Barcode generation failed for '{code}': {e}")
            continue

        temp_name = f"temp_barcode_{i}"
        barcode.save(temp_name)
        png_path = f"{temp_name}.png"
        temp_files.append(png_path)

        pdf.image(png_path, x=x_offset + 0.1, y=y_offset + 0.1, w=label_width - 0.2)
        pdf.set_xy(x_offset, y_offset + label_height / 2)
        pdf.set_font("Arial", "B", 20)
        pdf.multi_cell(label_width, 0.3, code, align="C")

        x_offset += label_width
        if (i + 1) % labels_per_row == 0:
            x_offset = 0
            y_offset += label_height

    output = BytesIO()
    pdf.output(output)
    output.seek(0)

    # Cleanup
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)

    return output

# -----------------------------
if generate_button:
    codes = generate_codes()
    if codes:
        st.success(f"Generated {len(codes)} bin labels successfully!")
        try:
            pdf_file = create_pdf(codes)
            st.download_button(
                "📥 Download PDF",
                pdf_file,
                file_name="bin_labels.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error: {str(e)}")
