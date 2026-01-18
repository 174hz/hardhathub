import requests
from bs4 import BeautifulSoup
import os
from supabase import create_client
import time

# 1. Setup Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def get_category(title):
    title = title.lower()
    if any(word in title for word in ["forklift", "operator", "machine", "pallet jack"]):
        return "Machinery & Forklift"
    elif any(word in title for word in ["picker", "packer", "sorting", "order"]):
        return "Picking & Packing"
    elif any(word in title for word in ["loader", "unloader", "handler", "handballer"]):
        return "Loading & Unloading"
    elif any(word in title for word in ["stock", "inventory", "receiving", "receiver", "clerk"]):
        return "Inventory & Stocking"
    elif any(word in title for word in ["mover", "helper", "logistics", "driver"]):
        return "Moving & Logistics"
    else:
        return "General Logistics"

def scrape_job_bank():
    # Focused keywords to ensure high-quality matches
    keywords = ["Warehouse", "Labor", "Forklift", "Packer", "Logistics"]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    for search_term in keywords:
        print(f"Deep Scanning for: {search_term}...")
        # Searching specifically for 'Verified' jobs to get better results
        search_url = f"https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={search_term}&locationstring=Canada&sort=M"
        
        try:
            response = requests.get(search_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for all results in the job results list
            articles = soup.select('article')
            
            if not articles:
                print(f"  [!] No articles found for {search_term}. Checking alternative tags...")
                articles = soup.find_all('a', class_='resultJobItem') # Backup selector

            for article in articles:
                try:
                    # More robust data extraction
                    title_elem = article.find('span', class_='title') or article.find('h3')
                    if not title_elem: continue
                    
                    title = title_elem.get_text().strip()
                    company = article.find('li', class_='business').get_text().strip() if article.find('li', class_='business') else "Confidential"
                    location = article.find('li', class_='location').get_text().strip() if article.find('li', class_='location') else "Canada"
                    
                    # Ensure we get the full link
                    link_elem = article.find('a') or article
                    link = "https://www.jobbank.gc.ca" + link_elem['href'] if 'href' in link_elem.attrs else ""
                    
                    if not link or "jobsearch" in link: continue

                    functional_category = get_category(title)
                    
                    job_data = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "link": link,
                        "job_type": "Verified",
                        "tags": [functional_category, search_term],
                        "posted_date": "Recently"
                    }
                    
                    # Upsert to Supabase
                    supabase.table("jobs").upsert(job_data, on_conflict="link").execute()
                    print(f"  [SUCCESS] Found: {title}")
                    
                except Exception as e:
                    continue
            
            time.sleep(2) # Be respectful to avoid blocks

        except Exception as e:
            print(f"  [ERROR] Problem reaching Job Bank for {search_term}: {e}")

if __name__ == "__main__":
    scrape_job_bank()
