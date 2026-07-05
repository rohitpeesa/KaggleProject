import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Dense boilerplate text to simulate a real RFP
boilerplate_paragraphs = [
    "1.1 Background and Objectives. The purpose of this Request for Proposal (RFP) is to solicit proposals from qualified vendors to provide comprehensive enterprise modernization services. The Government is seeking to leverage commercial best practices to modernize its legacy systems. Offerors shall provide a detailed approach that demonstrates an understanding of the complex operational environment.",
    "1.2 Scope of Work. The scope encompasses the full software development life cycle (SDLC), including requirements gathering, architecture design, agile development, testing, deployment, and operations and maintenance (O&M). The Contractor shall ensure all deliverables comply with federal accessibility standards and stringent security protocols.",
    "1.3 Applicable Documents. The Contractor must adhere to all documents listed in Attachment A, including but not limited to NIST SP 800-53 Rev 5, Federal Risk and Authorization Management Program (FedRAMP) guidelines, and internal agency policies regarding data governance and privacy.",
    "1.4 Personnel Requirements. Key personnel proposed for this contract must possess active security clearances and demonstrate a minimum of five years of relevant experience in their respective domains. The Contractor shall maintain a highly skilled workforce and provide a staffing plan that ensures continuity of operations.",
    "1.5 Performance Metrics. The Government will evaluate contractor performance based on Service Level Agreements (SLAs) defined in Section J. Metrics will include system uptime (99.99%), response times for critical incidents (under 15 minutes), and defect density rates in production releases.",
    "1.6 Invoicing and Payment. Invoices must be submitted electronically via the Invoice Processing Platform (IPP) on a monthly basis. Each invoice must include a detailed breakdown of labor hours, materials, and other direct costs incurred during the billing period.",
    "1.7 Transition Plan. Upon contract award, the Contractor must execute a seamless phase-in transition within 60 days, ensuring no disruption to ongoing mission-critical activities. A phase-out plan must also be provided at the end of the period of performance.",
    "1.8 Data Rights and Intellectual Property. The Government retains unlimited rights to all custom software, documentation, and data produced under this contract. The Contractor shall not incorporate proprietary code without prior written approval from the Contracting Officer.",
    "1.9 Security clearaces. All contract personnel must complete mandatory security awareness training before accessing government information systems. Non-disclosure agreements (NDAs) are required for all staff handling sensitive but unclassified (SBU) information.",
    "1.10 Quality Assurance. The Contractor shall implement a Quality Assurance Surveillance Plan (QASP) to monitor service delivery. The QASP must include regular audits, risk management frameworks, and continuous improvement methodologies."
]

def create_dense_rfp(filename, title, reqs, num_pages):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title Page
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, title)
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.3 * inch, "Solicitation Number: DEMO-2026-0001")
    
    y = height - 2 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y, "Table of Contents")
    y -= 0.3 * inch
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, y, "1. Introduction and Background..........Page 2")
    c.drawString(1 * inch, y - 0.2*inch, "2. Statement of Work....................Page 3")
    c.drawString(1 * inch, y - 0.4*inch, "3. Terms and Conditions.................Page 4")
    c.drawString(1 * inch, y - 0.6*inch, f"4. Technical Requirements...............Page {num_pages-1}")
    
    c.showPage()
    
    # Dense Pages
    for page_num in range(2, num_pages):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, height - 1 * inch, f"Section {page_num-1} - General Provisions (Page {page_num})")
        
        c.setFont("Helvetica", 10)
        y = height - 1.5 * inch
        
        # Write dense paragraphs
        for _ in range(3): # repeat to fill page
            for para in boilerplate_paragraphs:
                # Simple text wrapping logic
                words = para.split()
                line = ""
                for word in words:
                    if c.stringWidth(line + word + " ", "Helvetica", 10) < width - 2 * inch:
                        line += word + " "
                    else:
                        c.drawString(1 * inch, y, line)
                        y -= 0.15 * inch
                        line = word + " "
                        if y < 1 * inch: # Page is full
                            break
                c.drawString(1 * inch, y, line)
                y -= 0.25 * inch
                
                if y < 1 * inch:
                    break
            if y < 1 * inch:
                break
                
        c.showPage()
        
    # Requirements Page
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 1 * inch, f"Section {num_pages-1} - Mandatory Requirements (Page {num_pages})")
    
    y = height - 1.5 * inch
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, y, "The following requirements MUST be met by the vendor:")
    y -= 0.4 * inch
    
    for req in reqs:
        c.drawString(1 * inch, y, f"- {req}")
        y -= 0.3 * inch
        
    # Add some trailing dense text
    y -= 0.5 * inch
    c.setFont("Helvetica", 10)
    for para in boilerplate_paragraphs[:2]:
        words = para.split()
        line = ""
        for word in words:
            if c.stringWidth(line + word + " ", "Helvetica", 10) < width - 2 * inch:
                line += word + " "
            else:
                c.drawString(1 * inch, y, line)
                y -= 0.15 * inch
                line = word + " "
        c.drawString(1 * inch, y, line)
        y -= 0.25 * inch
        
    c.showPage()
    c.save()

if __name__ == "__main__":
    reqs_sam = [
        "The system must be deployed on GCP infrastructure.",
        "The core tech stack must utilize Python and Kubernetes.",
        "The contractor must hold an active ISO 27001 certification.",
        "The contractor must be actively pursuing FedRAMP authorization.",
        "The project must be completed within 12 months of award."
    ]
    create_dense_rfp("mock_sam_rfp.pdf", "Request for Proposal - Federal Health Data Platform", reqs_sam, 14)
    
    reqs_mock = [
        "The system must be deployed natively on AWS infrastructure.",
        "The backend must be written in Node.js.",
        "The contractor must hold a valid SOC 2 Type II certification.",
        "The project must be completed within 6 months."
    ]
    create_dense_rfp("mock_rfp.pdf", "Request for Proposal - Enterprise Cloud Migration", reqs_mock, 10)
