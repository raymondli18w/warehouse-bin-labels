import streamlit as st
from fpdf import FPDF
from io import BytesIO
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image

st.set_page_config(page_title="Warehouse Bin Label Generator", layout="wide")
st.title("Warehouse Bin Label Generator")

# --- User inputs ---
prefix = st.text_input("Prefix", value="16EA")
start_middle = st.text_input("Start Middle (comma-separated)", value="01")
start_aisle = st.text_input("Start Aisle", value="A")
start_level_letter = st.text_input("Start Level Letter (optional, comma-separated)", value="A")
start_level = st.text_input("Start Level (optional)", value="1")

end_middle = st.text_input("End Middle (comma-separated)", value="20")
end_aisle = st.text_input("End Aisle", value="A")
end_level_letter = st.text_input("End Level Letter (optional, comma-separated)", value="A")
end_level = st.text_input("End Level (optional)", value="5")

label_width = st.number_input("Label Width (inches)", value=4.0)
label_height = st.number_input("Label Height (inches)", value=6.0)

generate_button = st.button("Generate PDF Labels")

# --- Helper to create sequences ---
def generate_codes():
    middle_nums = range(int(start_middle), int(end_middle)+1)
    level_nums = range(int(start_level), int(end_level)+1) if start_level and end_level else [None]
    level_letters = start_level_letter.split(",") if start_level_letter else [None]

    codes = []
    for m in middle_nums:
        for ll in level_letters:
            for lv in level_nums:
                code = f"{prefix}{str(m).zfill(2)}"
                if ll:
                    code += f"{ll}"
                if lv is not None:
                    code += f"-{lv}"
                codes.append(code)
    return codes

# --- Generate PDF ---
def create_pdf(codes):
    pdf = FPDF(unit='in', format=(label_width, label_height))
    pdf.set_auto_page_break(False)

    for code in codes:
        pdf.add_page()
        # Barcode
        barcode_obj = Code128(code, writer=ImageWriter(), add_checksum=False)
        barcode_bytes = BytesIO()
        barcode_obj.write(barcode_bytes, {"module_height": 10, "quiet_zone": 2})
        barcode_bytes.seek(0)
        barcode_img = Image.open(barcode_bytes)
        img_path = BytesIO()
        barcode_img.save(img_path, format="PNG")
        img_path.seek(0)
        pdf.image(img_path, x=0.5, y=0.2, w=label_width-1.0)

        # Text below barcode
        pdf.set_font("Arial", "B", 36)
        pdf.set_y(label_height/2)
        pdf.multi_cell(0, 0.5, code, align="C")

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

if generate_button:
    codes = generate_codes()
    pdf_file = create_pdf(codes)
    st.download_button("Download PDF", pdf_file, file_name="bin_labels.pdf")
