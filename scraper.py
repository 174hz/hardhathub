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
    """Categorizes jobs based on functional tasks in the title"""
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
    # 2. Expanded Keywords based on your strategy
    keywords = ["Warehouse", "Loader", "Handler", "Picker", "Packer", "Stocker", "Unloader", "Logistics", "Material Mover", "Forklift"]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for search_term in keywords:
        print(f"Searching for: {search_term}...")
        search_url = f"https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={search_term}&locationstring=Canada"
        
        try:
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article')

            for article in articles:
                try:
                    title = article.find('span', class_='title').text.strip()
                    company = article.find('li', class_='business').text.strip()
                    location = article.find('li', class_='location').text.strip()
                    link = "https://www.jobbank.gc.ca" + article.find('a')['href']
                    
                    # Apply your new Categorization Strategy
                    functional_category = get_category(title)
                    
                    job_data = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "link": link,
                        "job_type": "Full-Time", # Default
                        "tags": [functional_category, search_term],
                        "posted_date": "Recently"
                    }
                    
                    # Upsert to Supabase (avoids duplicates based on the link)
                    supabase.table("jobs").upsert(job_data, on_conflict="link").execute()
                    print(f"  [+] Saved: {title} ({functional_category})")
                    
                except Exception as e:
                    continue # Skip individual listing errors
            
            # Brief pause to be respectful to the server
            time.sleep(1)

        except Exception as e:
            print(f"Error searching for {search_term}: {e}")

if __name__ == "__main__":
    scrape_job_bank()
