import requests
from bs4 import BeautifulSoup
import os
from supabase import create_client

# Setup Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def get_category(title):
    t = title.lower()
    if any(x in t for x in ["manager", "supervisor", "lead"]): return "Management"
    if any(x in t for x in ["forklift", "operator"]): return "Machinery & Forklift"
    if any(x in t for x in ["pack", "pick"]): return "Picking & Packing"
    return "Warehouse General"

def scrape():
    print(">>> INITIATING POSITIONAL RECOVERY SCAN <<<")
    # Search URL for Warehouse jobs in Canada
    search_url = "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=warehouse&locationstring=Canada&sort=M"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}

    try:
        response = requests.get(search_url, headers=headers, timeout=25)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Target the main job result containers
        articles = soup.find_all('article')
        print(f"Found {len(articles)} potential jobs. Extracting data...")

        for job in articles:
            try:
                # 1. Grab the title (usually the only span with 'title' or the first link text)
                title_elem = job.find('span', class_='title') or job.find('h3')
                if not title_elem: continue
                title = title_elem.get_text(strip=True).replace('Verified', '').replace('New', '').strip()

                # 2. Grab business and location by their list position
                # li:nth-child(1) is usually Company, li:nth-child(2) is usually Location
                details = job.find_all('li')
                company = details[0].get_text(strip=True) if len(details) > 0 else "Logistics Company"
                location = details[1].get_text(strip=True).replace('Location', '').strip() if len(details) > 1 else "Canada"

                # 3. Secure the link
                link_tag = job.find('a', href=True)
                if not link_tag: continue
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

                # Save to Supabase
                supabase.table("jobs").upsert(job_entry, on_conflict="link").execute()
                print(f"    [+] Successfully Saved: {title}")
                
            except Exception as e:
                # If one job fails, skip it and keep going
                continue
                
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    scrape()
