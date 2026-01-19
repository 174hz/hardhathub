import requests
from bs4 import BeautifulSoup
import os
from supabase import create_client

# Setup Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def scrape():
    print(">>> INITIATING RESILIENT SYNC <<<")
    # Using the mobile version of Job Bank which has a simpler, easier-to-scrape layout
    search_url = "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=warehouse+laborer&locationstring=Canada&sort=M"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}

    try:
        response = requests.get(search_url, headers=headers, timeout=25)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for any 'article' or 'a' tag that contains job data
        articles = soup.select('article')
        print(f"Found {len(articles)} job containers. Processing...")

        for job in articles:
            try:
                # 1. More flexible Title finding
                title_elem = job.select_one('.title, h3, .job-title')
                if not title_elem: continue
                title = title_elem.get_text(strip=True).replace('Verified', '').strip()

                # 2. Flexible Company finding
                company_elem = job.select_one('.business, .company, li:nth-of-type(1)')
                company = company_elem.get_text(strip=True) if company_elem else "Direct Hire"

                # 3. Flexible Location finding
                location_elem = job.select_one('.location, li:nth-of-type(2)')
                location = "Canada"
                if location_elem:
                    location = location_elem.get_text(strip=True).replace('Location', '').strip()
                
                # 4. Link finding
                link_tag = job.find('a', href=True)
                if not link_tag: continue
                raw_link = link_tag['href'].split(';')[0]
                full_link = "https://www.jobbank.gc.ca" + raw_link if not raw_link.startswith('http') else raw_link

                # Tagging logic
                tag = "Moving & Logistics"
                if any(x in title.lower() for x in ["forklift", "operator"]): tag = "Machinery & Forklift"
                elif any(x in title.lower() for x in ["pack", "pick"]): tag = "Picking & Packing"

                job_entry = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": full_link,
                    "tags": [tag],
                    "job_type": "Full-Time"
                }

                # Save to Supabase
                supabase.table("jobs").upsert(job_entry, on_conflict="link").execute()
                print(f"    [+] Successfully Saved: {title}")
                
            except Exception as e:
                print(f"    [!] Internal Error on item: {e}")
                continue
                
    except Exception as e:
        print(f"CRITICAL SCRAPE ERROR: {e}")

if __name__ == "__main__":
    scrape()
