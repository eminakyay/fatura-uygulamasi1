
from flask import Flask, render_template, request, send_file
import pandas as pd
from fpdf import FPDF
import os
import zipfile
import tempfile

app = Flask(__name__)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

class PDF(FPDF):
    def header(self):
        self.set_font('DejaVu', '', 16)
        self.cell(0, 10, 'Invoice', ln=True, align='L')
        self.ln(5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    file = request.files['file']
    if not file:
        return "No file uploaded"

    df = pd.read_csv(file)
    df.columns = [col.strip() for col in df.columns]
    df = df[["Kaynak ismi", "Kaynak miktar", "Tamamlandığı tarih", "Açıklama"]].copy()
    df.columns = ["Name", "Amount", "Date", "Reference"]
    df["Name"] = df["Name"].astype(str)

    tmp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(tmp_dir, "invoices.zip")
    invoice_dir = os.path.join(tmp_dir, "pdfs")
    os.makedirs(invoice_dir)

    for idx, row in df.iterrows():
        name = row["Name"]
        amount = row["Amount"]
        date = row["Date"]
        reference = str(row["Reference"])
        invoice_number = f"INV-{1000 + idx}"

        pdf = PDF()
        pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
        pdf.add_font("DejaVu", "B", FONT_BOLD_PATH, uni=True)
        pdf.add_page()
        pdf.set_font("DejaVu", '', 12)

        pdf.set_xy(150, 10)
        pdf.multi_cell(0, 8, f"Invoice number\n{invoice_number}", align="R")
        pdf.set_xy(150, 25)
        pdf.multi_cell(0, 8, f"Issue date\n{date}", align="R")

        pdf.ln(30)
        pdf.set_font("DejaVu", '', 12)
        pdf.cell(40, 10, "Billed to", ln=True)
        pdf.set_font("DejaVu", 'B', 12)
        pdf.cell(100, 10, name, ln=True)

        pdf.ln(10)
        pdf.set_font("DejaVu", '', 12)
        pdf.cell(0, 10, f"{amount:.0f} TRY due by {date}", ln=True)

        pdf.ln(10)
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(60, 10, "Product or service")
        pdf.cell(30, 10, "Quantity")
        pdf.cell(40, 10, "Unit price")
        pdf.cell(40, 10, "Total", ln=True)

        pdf.set_font("DejaVu", "", 12)
        pdf.cell(60, 10, "service")
        pdf.cell(30, 10, "1")
        pdf.cell(40, 10, f"{amount:.2f} TRY")
        pdf.cell(40, 10, f"{amount:.2f} TRY", ln=True)

        pdf.ln(10)
        pdf.cell(170, 10, f"Total excluding tax: {amount:.2f} TRY", ln=True)
        pdf.cell(170, 10, f"Total tax: 0.00 TRY", ln=True)
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(170, 10, f"Amount Due: {amount:.2f} TRY", ln=True)

        pdf.ln(10)
        pdf.set_font("DejaVu", '', 11)
        pdf.cell(100, 10, "Issued by:")
        pdf.ln(6)
        pdf.cell(100, 10, "Benjamin Danismanlik OÜ")
        pdf.ln(5)
        pdf.cell(100, 10, "Harju maakond, Tallinn, Lasnamäe linnaosa")
        pdf.ln(5)
        pdf.cell(100, 10, "Ruunaoja tn 3, 11415 – Estonia")

        filename = f"{invoice_number}_{name.replace(' ', '_')}.pdf"
        pdf.output(os.path.join(invoice_dir, filename))

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for fname in os.listdir(invoice_dir):
            zipf.write(os.path.join(invoice_dir, fname), arcname=fname)

    return send_file(zip_path, as_attachment=True, download_name="invoices.zip")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
