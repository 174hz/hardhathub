import requests
from bs4 import BeautifulSoup
import os
from supabase import create_client
import time

# Setup Supabase
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
    # Searching Indeed Canada for manual labor roles
    search_url = "https://ca.indeed.com/jobs?q=warehouse+laborer&l=Canada&sort=date"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }

    print("Initiating National Logistics Scan via Indeed...")
    
    try:
        # We use a shorter timeout here to fail fast if blocked
        res = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Indeed's job card selector
        jobs = soup.find_all('div', class_='job_seen_beacon')
        print(f"Detected {len(jobs)} active listings...")

        for job in jobs:
            try:
                title_node = job.find('h2')
                if not title_node: continue
                title = title_node.get_text(strip=True)

                company_node = job.find('span', attrs={'data-testid': 'company-name'})
                company = company_node.get_text(strip=True) if company_node else "Direct Hire"

                location_node = job.find('div', attrs={'data-testid': 'text-location'})
                location = location_node.get_text(strip=True) if location_node else "Canada"
                
                link_node = job.find('a')
                link = "https://ca.indeed.com" + link_node['href'] if link_node else ""

                if not link: continue

                category = get_category(title)
                
                data = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "tags": [category, "Verified"],
                    "job_type": "Full-Time"
                }

                # Save to your database
                supabase.table("jobs").upsert(data, on_conflict="link").execute()
                print(f"    [+] Logged: {title}")
            except Exception as e:
                continue

    except Exception as e:
        print(f"Scan interrupted: {e}")

if __name__ == "__main__":
    scrape()
