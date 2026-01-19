import requests
from bs4 import BeautifulSoup
import os
from supabase import create_client

# Setup Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def scrape():
    print(">>> STARTING FORCE SYNC <<<")
    search_url = "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=warehouse+laborer&locationstring=Canada&sort=M"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}

    try:
        response = requests.get(search_url, headers=headers, timeout=25)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')
        
        print(f"Found {len(articles)} jobs on Job Bank.")

        for job in articles:
            try:
                title = job.find('span', class_='title').get_text(strip=True)
                # Cleaning the title of extra words
                title = title.replace('Verified', '').strip()
                
                company = job.find('li', class_='business').get_text(strip=True) if job.find('li', class_='business') else "Direct Hire"
                location = job.find('li', class_='location').get_text(strip=True).replace('Location', '').strip()
                link_suffix = job.find('a')['href'].split(';')[0]
                link = "https://www.jobbank.gc.ca" + link_suffix

                job_entry = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "tags": ["Moving & Logistics", "Verified"], # Default tag for now
                    "job_type": "Full-Time"
                }

                # Using insert instead of upsert for a cleaner test
                res = supabase.table("jobs").insert(job_entry).execute()
                print(f"    [+] Successfully Saved: {title}")
                
            except Exception as e:
                print(f"    [!] Skip item: {e}")
                continue
                
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    scrape()
