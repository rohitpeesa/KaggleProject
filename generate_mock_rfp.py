from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Create a realistic replacement for mock_rfp.pdf
c = canvas.Canvas("mock_rfp.pdf", pagesize=letter)
c.setFont("Helvetica-Bold", 16)
c.drawString(100, 750, "Request for Proposal (RFP) - Enterprise Cloud Migration")
c.setFont("Helvetica", 12)
c.drawString(100, 730, "Solicitation Number: AWS-2026-MIG-009")

# Pad with 8 empty pages to simulate a large document
for i in range(1, 9):
    c.drawString(100, 700, f"Section {i}: General Terms and Conditions")
    c.drawString(100, 650, "Standard boilerplate text... This is a 10-page document.")
    c.showPage()

# Page 9 - Technical Requirements
c.setFont("Helvetica-Bold", 14)
c.drawString(100, 750, "9. Technical Requirements")
c.setFont("Helvetica", 12)
c.drawString(100, 710, "- The system must be deployed natively on AWS infrastructure.")
c.drawString(100, 680, "- The backend must be written in Node.js.")

# Page 10 - Compliance & Timeline
c.showPage()
c.setFont("Helvetica-Bold", 14)
c.drawString(100, 750, "10. Compliance and Timeline")
c.setFont("Helvetica", 12)
c.drawString(100, 710, "- The contractor must hold a valid SOC 2 Type II certification.")
c.drawString(100, 680, "- The project must be completed within 6 months.")

c.save()
