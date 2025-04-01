from xhtml2pdf import pisa
from io import BytesIO

html_content = """
<!DOCTYPE html>
<html>
<body>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"/>

<div class="text-center border-bottom">
  <p class="h4 fw-bold mb-0">FALAK PUBLIC SCHOOL, MORADABAD</p>
  <p class="h5 fw-bold mb-0"></p>
  <p class="h6 fw-bold mb-0">Subject - </p>
</div>
</body>
</html>

"""
pdf_output = BytesIO()

pisa.CreatePDF(html_content, dest=pdf_output, encoding='utf-8')

with open("html-to-pdf.pdf", "wb") as pdf_file:
  
  pdf_file.write(pdf_output.getvalue())