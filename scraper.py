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
    # We are using a simpler, broader search URL that is harder to block
    search_terms = ["warehouse", "labor", "forklift"]
    
    # "Super-Agent" headers to look like a real person
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }

    for term in search_terms:
        print(f"Searching for {term}...")
        # New URL format that Job Bank prefers
        url = f"https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={term}&locationstring=Canada"
        
        try:
            res = requests.get(url, headers=headers, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # This is the "Magic" selector that finds Job Bank entries
            results = soup.find_all('article')
            
            print(f"  Found {len(results)} potential items...")

            for job in results:
                try:
                    title = job.find('span', class_='title').get_text(strip=True)
                    company = job.find('li', class_='business').get_text(strip=True)
                    location = job.find('li', class_='location').get_text(strip=True)
                    link = "https://www.jobbank.gc.ca" + job.find('a')['href'].split(';')[0]

                    category = get_category(title)
                    
                    data = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "link": link,
                        "tags": [category, term.capitalize()],
                        "job_type": "Verified"
                    }

                    supabase.table("jobs").upsert(data, on_conflict="link").execute()
                    print(f"    [+] Saved: {title}")
                except:
                    continue
                    
            time.sleep(3) # Slow down to stay under the radar

        except Exception as e:
            print(f"  [!] Error: {e}")

if __name__ == "__main__":
    scrape()
