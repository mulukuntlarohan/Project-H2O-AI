import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import re

def get_specs_data(dc_url):
    """Visits the /specs/ page of a data center and extracts MW and SqFt."""
    spec_url = dc_url.rstrip('/') + "/specs/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        time.sleep(1) # Be respectful to the server
        response = requests.get(spec_url, headers=headers)
        if response.status_code != 200:
            return "N/A", "N/A"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text()

        # Regex for Megawatts (e.g., 24 MW)
        mw_match = re.search(r'(\d+\.?\d*)\s?MW', text_content)
        capacity_mw = mw_match.group(0) if mw_match else "N/A"

        # Regex for Square Footage (e.g., 150,000 sq.f.)
        sqft_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s?sq\.?f', text_content)
        area_sqft = sqft_match.group(0) if sqft_match else "N/A"

        return capacity_mw, area_sqft
    except:
        return "Error", "Error"

def scrape_houston_refined():
    base_url = "https://www.datacentermap.com/usa/texas/houston/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    print("Phase 1: Fetching and Splitting Name/Address...")
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    dc_entries = []
    
    # On DataCenterMap, each entry is typically inside a div with a specific class or structure
    # We look for the links and then extract the sub-header address from their parent container
    for link in soup.find_all('a'):
        href = link.get('href', '')
        # Filter for data center profile links
        if '/usa/texas/houston/' in href and href.count('/') > 4:
            # The Name is the text inside the <a> tag
            dc_name = link.text.strip()
            
            # The Address is usually in a sibling or parent element (the sub-header)
            # We try to find the address text near the link
            parent_container = link.find_parent(['div', 'td', 'li'])
            address = "N/A"
            if parent_container:
                # Often the address is in a 'span' or 'div' with a smaller font class
                sub_header = parent_container.find(['span', 'p', 'div'], class_=re.compile(r'sub|address|text-muted', re.I))
                if sub_header:
                    address = sub_header.text.strip()
                else:
                    # Fallback: check the text within the parent container excluding the link text
                    all_text = parent_container.get_text(separator='|').split('|')
                    if len(all_text) > 1:
                        address = all_text[1].strip()

            full_url = "https://www.datacentermap.com" + href
            dc_entries.append({
                "Name": dc_name, 
                "Address": address,
                "URL": full_url
            })

    # Convert to DataFrame and drop duplicates
    df_list = pd.DataFrame(dc_entries).drop_duplicates(subset=['Name']).to_dict('records')
    
    print(f"Phase 2: Extracting MW and SqFt for {len(df_list)} entries...")
    
    final_results = []
    for dc in df_list:
        print(f"Working on: {dc['Name']}...")
        mw, sqft = get_specs_data(dc['URL'])
        
        final_results.append({
            "Data_Center_Name": dc['Name'],
            "Address": dc['Address'],
            "Capacity_MW": mw,
            "Area_SqFt": sqft,
            "Source_URL": dc['URL']
        })

    # Save to your specific folder
    output_path = r"C:\Users\M.THIRUPATHI\Desktop\Internship\Project-H2O-AI\data\houston_data_centers_final.xlsx"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df = pd.DataFrame(final_results)
    df.to_excel(output_path, index=False)
    
    print("-" * 30)
    print(f"SUCCESS! Separate columns created.")
    print(f"File: {output_path}")

if __name__ == "__main__":
    scrape_houston_refined()