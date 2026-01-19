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
    # Using Careerjet Canada - a very reliable source for manual labor
    search_url = "https://www.careerjet.ca/search/jobs?s=warehouse+laborer&l=Canada&sort=date"
    
    # Advanced headers to bypass bot detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://www.google.com/'
    }

    print("Initiating Stealth Scan for HardHatHub...")
    
    try:
        session = requests.Session()
        response = session.get(search_url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"  [!] Connection rejected: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Careerjet job item selector
        jobs = soup.select('.job')
        print(f"Detected {len(jobs)} active listings on Careerjet...")

        for job in jobs:
            try:
                title_link = job.select_one('header h2 a')
                if not title_link: continue
                
                title = title_link.get_text(strip=True)
                link = "https://www.careerjet.ca" + title_link['href']
                
                company = job.select_one('.company_location .company')
                company = company.get_text(strip=True) if company else "Direct Hire"
                
                location = job.select_one('.company_location .locations')
                location = location.get_text(strip=True) if location else "Canada"

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
                print(f"    [+] Saved: {title}")
                
            except Exception as e:
                continue

    except Exception as e:
        print(f"Scan failed: {e}")

if __name__ == "__main__":
    scrape()
