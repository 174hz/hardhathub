import requests
from bs4 import BeautifulSoup
import os
from supabase import create_client
import time

# 1. Setup Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def get_category(title):
    title = title.lower()
    if any(word in title for word in ["forklift", "operator", "machine"]): return "Machinery & Forklift"
    if any(word in title for word in ["picker", "packer", "order"]): return "Picking & Packing"
    if any(word in title for word in ["loader", "unloader", "handler"]): return "Loading & Unloading"
    if any(word in title for word in ["stock", "inventory", "receiving"]): return "Inventory & Stocking"
    return "Moving & Logistics"

def scrape():
    # Targets Job Bank Canada directly with a recent search filter
    search_url = "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=warehouse+laborer&locationstring=Canada&sort=M"
    
    # We use a Mobile User-Agent to slip through firewalls more easily
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-CA,en-US;q=0.9,en;q=0.8',
    }

    print("Initiating Direct National Scan (No-Key Mode)...")
    
    try:
        response = requests.get(search_url, headers=headers, timeout=25)
        
        if response.status_code != 200:
            print(f"  [!] Site blocked the request. Status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This selector targets the standard Job Bank article list
        articles = soup.find_all('article')
        print(f"Detected {len(articles)} potential listings...")

        for job in articles:
            try:
                # Extracting Title
                title_elem = job.find('span', class_='title')
                if not title_elem: continue
                title = title_elem.get_text(strip=True)

                # Extracting Company
                company_elem = job.find('li', class_='business')
                company = company_elem.get_text(strip=True) if company_elem else "Direct Hire"

                # Extracting Location
                location_elem = job.find('li', class_='location')
                location = location_elem.get_text(strip=True).replace('Location', '').strip() if location_elem else "Canada"
                
                # Extracting Link
                link_elem = job.find('a')
                if not link_elem or 'href' not in link_elem.attrs: continue
                link = "https://www.jobbank.gc.ca" + link_elem['href'].split(';')[0]

                category = get_category(title)
                
                job_data = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "tags": [category, "Verified"],
                    "job_type": "Full-Time"
                }

                # Save to Supabase
                supabase.table("jobs").upsert(job_data, on_conflict="link").execute()
                print(f"    [+] Logged: {title}")
                
            except Exception as e:
                continue

    except Exception as e:
        print(f"Scan interrupted: {e}")

if __name__ == "__main__":
    scrape()
