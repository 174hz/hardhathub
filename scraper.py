import requests
from bs4 import BeautifulSoup
import os
from supabase import create_client
from datetime import datetime, timedelta

# Setup Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def auto_cleanup():
    """Deletes job postings older than 14 days"""
    threshold = (datetime.now() - timedelta(days=14)).isoformat()
    try:
        supabase.table("jobs").delete().lt("created_at", threshold).execute()
        print(f">>> Auto-Cleanup: Removed expired listings older than {threshold}")
    except Exception as e:
        print(f"Cleanup Error: {e}")

def get_category(title):
    title = title.lower()
    if any(word in title for word in ["forklift", "operator", "machine"]): return "Machinery & Forklift"
    if any(word in title for word in ["picker", "packer", "order"]): return "Picking & Packing"
    if any(word in title for word in ["loader", "unloader", "handler"]): return "Loading & Unloading"
    if any(word in title for word in ["stock", "inventory", "receiving"]): return "Inventory & Stocking"
    return "Moving & Logistics"

def scrape():
    # 1. Run Cleanup First
    auto_cleanup()

    print("Initiating Direct National Scan (No-Key Mode)...")
    search_url = "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=warehouse+laborer&locationstring=Canada&sort=M"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'}

    try:
        response = requests.get(search_url, headers=headers, timeout=25)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')

        for job in articles:
            try:
                title_elem = job.find('span', class_='title')
                if not title_elem: continue
                title = title_elem.get_text(strip=True)

                company_elem = job.find('li', class_='business')
                company = company_elem.get_text(strip=True) if company_elem else "Direct Hire"

                location_elem = job.find('li', class_='location')
                location = location_elem.get_text(strip=True).replace('Location', '').strip() if location_elem else "Canada"
                
                link_elem = job.find('a')
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

                supabase.table("jobs").upsert(job_data, on_conflict="link").execute()
                print(f"    [+] Logged: {title}")
                
            except Exception: continue
    except Exception as e:
        print(f"Scan failed: {e}")

if __name__ == "__main__":
    scrape()
      
