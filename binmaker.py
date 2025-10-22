import streamlit as st
from fpdf import FPDF
from io import BytesIO
from barcode import Code128
from barcode.writer import ImageWriter
import re

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

label_width = st.number_input("Label Width (inches)", value=4.0)
label_height = st.number_input("Label Height (inches)", value=6.0)
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
        st.error("Start/End Middle must be numbers.")
        return []

    try:
        level_nums = range(int(start_level), int(end_level) + 1) if start_level and end_level else [None]
    except ValueError:
        st.error("Level fields must be numeric if provided.")
        return []

    level_letters = [s.strip().upper() for s in start_level_letter.split(",")] if start_level_letter else [None]

    codes = []
    for m in middle_nums:
        for ll in level_letters:
            for lv in level_nums:
                parts = [prefix, f"{m:02d}"]
                if ll:
                    parts.append(ll)
                display_code = "".join(parts)
                if lv is not None:
                    display_code += f"-{lv}"
                # For barcode: remove hyphen (Code128 supports it, but python-barcode chokes on it)
                barcode_data = display_code.replace("-", "")
                # Validate: only A-Z, 0-9
                if re.fullmatch(r"[A-Z0-9]+", barcode_data):
                    codes.append((display_code, barcode_data))
    return codes

# -----------------------------
def create_pdf(codes):
    page_width = label_width * labels_per_row
    page_height = label_height * labels_per_column
    pdf = FPDF(unit="in", format=(page_width, page_height))
    pdf.set_auto_page_break(False)

    for i, (display_code, barcode_data) in enumerate(codes):
        if i % (labels_per_row * labels_per_column) == 0:
            pdf.add_page()
            x_offset = 0
            y_offset = 0

        # Generate barcode using python-barcode (no hyphen!)
        barcode = Code128(barcode_data, writer=ImageWriter(), add_checksum=True)
        barcode_file = f"barcode_{i}"
        barcode.save(barcode_file)  # saves as PNG

        # Add to PDF
        pdf.image(f"{barcode_file}.png", x=x_offset + 0.1, y=y_offset + 0.1, w=label_width - 0.2)
        pdf.set_xy(x_offset, y_offset + label_height / 2)
        pdf.set_font("Arial", "B", 20)
        pdf.multi_cell(label_width, 0.3, display_code, align="C")

        # Update position
        x_offset += label_width
        if (i + 1) % labels_per_row == 0:
            x_offset = 0
            y_offset += label_height

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
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
