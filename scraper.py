import requests
from bs4 import BeautifulSoup
import os
from supabase import create_client

# Setup Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def get_category(title):
    title_low = title.lower()
    if any(word in title_low for word in ["manager", "supervisor", "lead"]): return "Management"
    if any(word in title_low for word in ["forklift", "operator"]): return "Machinery & Forklift"
    if any(word in title_low for word in ["pack", "pick"]): return "Picking & Packing"
    return "Warehouse General"

def scrape():
    print(">>> INITIATING BRUTE-FORCE SYNC <<<")
    search_url = "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=warehouse&locationstring=Canada&sort=M"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}

    try:
        response = requests.get(search_url, headers=headers, timeout=25)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')
        
        print(f"Found {len(articles)} containers. Attempting extraction...")

        for job in articles:
            try:
                # 1. FIND TITLE: Look for the first span or heading available
                title_elem = job.find('span', class_='title') or job.find('h3') or job.find('span')
                title = title_elem.get_text(strip=True).replace('Verified', '').strip()

                # 2. FIND COMPANY: Job Bank often puts this in the first 'li' inside the 'ul'
                details = job.find_all('li')
                company = "Direct Hire"
                location = "Canada"
                
                if len(details) >= 1:
                    company = details[0].get_text(strip=True)
                if len(details) >= 2:
                    location = details[1].get_text(strip=True).replace('Location', '').strip()

                # 3. FIND LINK
                link_tag = job.find('a', href=True)
                raw_link = link_tag['href'].split(';')[0]
                full_link = "https://www.jobbank.gc.ca" + raw_link if not raw_link.startswith('http') else raw_link

                job_entry = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": full_link,
                    "tags": [get_category(title)],
                    "job_type": "Full-Time"
                }

                supabase.table("jobs").upsert(job_entry, on_conflict="link").execute()
                print(f"    [+] Saved: {title}")
                
            except Exception as e:
                continue # Skip if an individual job is too messy
                
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    scrape()
