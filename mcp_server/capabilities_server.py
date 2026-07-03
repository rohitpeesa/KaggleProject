import json
import os
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("CompanyCapabilities")

# Load company data
# Calculate the absolute path to data/company_profile.json
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, 'data', 'company_profile.json')

with open(data_path, 'r', encoding='utf-8') as f:
    company_data = json.load(f)

@mcp.tool()
def query_company_capabilities(domain: str) -> str:
    """
    Looks up our capabilities by domain keyword (case-insensitive).
    Returns matching capabilities as a formatted string.
    If no match, return "No specific capabilities found for domain: {domain}".
    """
    domain_lower = domain.lower()
    capabilities = []
    
    # Check domains of expertise
    for exp in company_data.get("domains_of_expertise", []):
        if domain_lower in exp.lower():
            capabilities.append(f"- Domain Expertise: {exp}")
            
    if not capabilities:
        return f"No specific capabilities found for domain: {domain}"
        
    return "\n".join(capabilities)

@mcp.tool()
def check_certification(cert_name: str) -> str:
    """
    Checks if the company holds a specific certification.
    Returns:
    - "CERTIFIED - Active" if we hold it
    - "NOT CERTIFIED" if we don't
    - "IN PROGRESS - Not yet active" if it's being pursued
    """
    cert_name_lower = cert_name.lower()
    
    # Gather all certs
    certs = company_data.get("security_certifications", {})
    comp = company_data.get("compliance_frameworks", {})
    
    all_certs = {k.lower(): v for k, v in certs.items()}
    all_certs.update({k.lower(): v for k, v in comp.items()})
    
    if cert_name_lower in all_certs:
        status = all_certs[cert_name_lower].lower()
        if status == "active":
            return "CERTIFIED - Active"
        elif status == "in progress":
            return "IN PROGRESS - Not yet active"
            
    return "NOT CERTIFIED"

if __name__ == '__main__':
    mcp.run()
