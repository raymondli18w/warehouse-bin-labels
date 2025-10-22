import streamlit as st
from fpdf import FPDF
from io import BytesIO
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image

# -----------------------------
# Streamlit App Configuration
# -----------------------------
st.set_page_config(page_title="Warehouse Bin Label Generator", layout="wide")
st.title("🏷️ Warehouse Bin Label Generator")

# --- User inputs ---
prefix = st.text_input("Prefix", value="16EA")
start_middle = st.text_input("Start Middle (number)", value="21")
end_middle = st.text_input("End Middle (number)", value="32")
start_level_letter = st.text_input("Start Level Letter (optional, comma-separated)", value="")
start_level = st.text_input("Start Level (optional, numeric)", value="1")
end_level_letter = st.text_input("End Level Letter (optional, comma-separated)", value="")
end_level = st.text_input("End Level (optional, numeric)", value="1")

label_width = st.number_input("Label Width (inches)", value=4.0)
label_height = st.number_input("Label Height (inches)", value=6.0)

generate_button = st.button("Generate PDF Labels")

# -----------------------------
# Helper: Generate Codes
# -----------------------------
def generate_codes():
    # Validate input
    if not start_middle or not end_middle:
        st.error("Please enter numeric values for both 'Start Middle' and 'End Middle'.")
        return []

    try:
        middle_nums = range(int(start_middle), int(end_middle) + 1)
    except ValueError:
        st.error("Start/End Middle must be numbers (e.g., 1 and 20).")
        return []

    try:
        level_nums = range(int(start_level), int(end_level) + 1) if start_level and end_level else [None]
    except ValueError:
        st.error("Level fields must be numeric if provided.")
        return []

    level_letters = start_level_letter.split(",") if start_level_letter else [None]
    end_level_letters = end_level_letter.split(",") if end_level_letter else [None]

    codes = []
    for m in middle_nums:
        for ll in (level_letters or [None]):
            for lv in level_nums:
                code = f"{prefix}{str(m).zfill(2)}"
                if ll:
                    code += f"{ll}"
                if lv is not None:
                    code += f"-{lv}"
                codes.append(code)
    return codes

# -----------------------------
# Helper: Create PDF
# -----------------------------
def create_pdf(codes):
    pdf = FPDF(unit='in', format=(label_width, label_height))
    pdf.set_auto_page_break(False)

    for code in codes:
        pdf.add_page()
        # Generate barcode
        barcode_obj = Code128(code, writer=ImageWriter(), add_checksum=False)
        barcode_bytes = BytesIO()
        barcode_obj.write(barcode_bytes, {"module_height": 10, "quiet_zone": 2})
        barcode_bytes.seek(0)
        barcode_img = Image.open(barcode_bytes)

        # Save image to temp path in memory
        img_temp = BytesIO()
        barcode_img.save(img_temp, format="PNG")
        img_temp.seek(0)

        # Add to PDF (FPDF requires filename, so save temporarily)
        barcode_img.save("temp_barcode.png", format="PNG")
        pdf.image("temp_barcode.png", x=0.5, y=0.2, w=label_width - 1.0)

        # Add text below barcode
        pdf.set_font("Arial", "B", 36)
        pdf.set_y(label_height / 2)
        pdf.multi_cell(0, 0.5, code, align="C")

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# -----------------------------
# Main: Generate Button
# -----------------------------
if generate_button:
    codes = generate_codes()
    if codes:
        st.success(f"Generated {len(codes)} bin labels successfully!")
        pdf_file = create_pdf(codes)
        st.download_button(
            "📥 Download PDF",
            pdf_file,
            file_name="bin_labels.pdf",
            mime="application/pdf"
        )
