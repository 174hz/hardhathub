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
    if any(word in title_low for word in ["manager", "supervisor", "lead"]): 
        return "Management"
    if any(word in title_low for word in ["forklift", "operator", "machine"]): 
        return "Machinery & Forklift"
    if any(word in title_low for word in ["picker", "packer", "order"]): 
        return "Picking & Packing"
    return "Warehouse General"

def scrape():
    print(">>> INITIATING CORRECTED COLUMN SYNC <<<")
    # Updated URL to ensure we get the most recent listings
    search_url = "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=warehouse&locationstring=Canada&sort=M"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}

    try:
        response = requests.get(search_url, headers=headers, timeout=25)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')
        
        print(f"Found {len(articles)} jobs. Processing...")

        for job in articles:
            try:
                # 1. Clean Title (Removing source prefixes)
                title_raw = job.find('span', class_='title').get_text(strip=True)
                title = title_raw.replace('Verified', '').replace('New', '').strip()
                
                # 2. Corrected Company Finder
                # In Job Bank, the company is usually the first <li> with class 'business'
                company_elem = job.find('li', class_='business')
                company = company_elem.get_text(strip=True) if company_elem else "Direct Hire"

                # 3. Corrected Location Finder
                location_elem = job.find('li', class_='location')
                location = "Canada"
                if location_elem:
                    # Removes the 'Location' label often found in the text
                    location = location_elem.get_text(strip=True).replace('Location', '').strip()
                
                # 4. Link Cleaning
                link_tag = job.find('a', href=True)
                raw_link = link_tag['href'].split(';')[0]
                full_link = "https://www.jobbank.gc.ca" + raw_link if not raw_link.startswith('http') else raw_link

                # 5. Tag Generation
                category = get_category(title)
                
                job_entry = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": full_link,
                    "tags": [category],
                    "job_type": "Full-Time"
                }

                # Save to Supabase
                supabase.table("jobs").upsert(job_entry, on_conflict="link").execute()
                print(f"    [+] Correctly Saved: {title} | Co: {company}")
                
            except Exception as e:
                print(f"    [!] Error processing item: {e}")
                continue
                
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    scrape()
