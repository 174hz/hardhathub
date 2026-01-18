import requests
from bs4 import BeautifulSoup
import os
from supabase import create_client

# 1. Setup Supabase (These will be added to your GitHub Secrets later)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def scrape_job_bank():
    # Searching for 'Warehouse' in 'Canada'
    search_url = "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=warehouse&locationstring=Canada"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    jobs = []
    # Job Bank uses 'article' tags for each listing
    articles = soup.find_all('article')

    for article in articles:
        try:
            title = article.find('span', class_='title').text.strip()
            company = article.find('li', class_='business').text.strip()
            location = article.find('li', class_='location').text.strip()
            link = "https://www.jobbank.gc.ca" + article.find('a')['href']
            
            # Simple logic to determine job type based on title/meta
            # Usually, Job Bank has specific tags we can parse
            job_type = "Full-Time" # Defaulting for now
            
            job_data = {
                "title": title,
                "company": company,
                "location": location,
                "link": link,
                "job_type": job_type,
                "tags": ["Warehouse", "Manual Labor"],
                "posted_date": "Recently"
            }
            
            # Send to Supabase
            supabase.table("jobs").upsert(job_data, on_conflict="link").execute()
            print(f"Saved: {title}")
            
        except Exception as e:
            print(f"Skipping a listing due to error: {e}")

if __name__ == "__main__":
    scrape_job_bank()
