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
    # Switching to a more accessible Canadian job feed
    search_url = "https://ca.indeed.com/jobs?q=warehouse+labor&l=Canada&sort=date"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    print("Initiating National Logistics Scan...")
    
    try:
        res = requests.get(search_url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Indeed uses a specific class for their job cards
        jobs = soup.find_all('div', class_='job_seen_beacon')
        print(f"Detected {len(jobs)} active listings...")

        for job in jobs:
            try:
                title = job.find('h2').get_text(strip=True)
                company = job.find('span', attrs={'data-testid': 'company-name'}).get_text(strip=True)
                location = job.find('div', attrs={'data-testid': 'text-location'}).get_text(strip=True)
                
                # Get the link
                link_tag = job.find('a')
                link = "https://ca.indeed.com" + link_tag['href']

                category = get_category(title)
                
                data = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "tags": [category, "Verified"],
                    "job_type": "Full-Time"
                }

                supabase.table("jobs").upsert(data, on_conflict="link").execute()
                print(f"    [+] Logged: {title}")
            except Exception as e:
                continue

    except Exception as e:
        print(f"Scan interrupted: {e}")

if __name__ == "__main__":
    scrape()
