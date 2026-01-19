import requests
import os
from supabase import create_client

# 1. Setup Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# 2. ADZUNA API CREDENTIALS
# I have cleaned these to ensure no extra spaces exist
ADZUNA_APP_ID = "767ae6dd"
ADZUNA_APP_KEY = "70924a39e11a69130b6042d703ed2266"

def get_category(title):
    title = title.lower()
    if any(word in title for word in ["forklift", "operator", "machine"]): return "Machinery & Forklift"
    if any(word in title for word in ["picker", "packer", "order"]): return "Picking & Packing"
    if any(word in title for word in ["loader", "unloader", "handler"]): return "Loading & Unloading"
    if any(word in title for word in ["stock", "inventory", "receiving"]): return "Inventory & Stocking"
    return "Moving & Logistics"

def scrape():
    print("Initiating Connection to Adzuna Canada...")
    
    # We move the keys into a 'params' dictionary which requests handles safely
    api_url = "https://api.adzuna.com/v1/api/jobs/ca/search/1"
    
    query_params = {
        "app_id": ADZUNA_APP_ID.strip(),
        "app_key": ADZUNA_APP_KEY.strip(),
        "results_per_page": 50,
        "what": "warehouse laborer",
        "content-type": "application/json"
    }
    
    try:
        # Performing the request with explicit parameters
        response = requests.get(api_url, params=query_params, timeout=20)
        
        if response.status_code == 401:
            print("  [!] AUTH ERROR: Keys are still being rejected.")
            print("  Tip: Check your email for a 'Verify Account' link from Adzuna.")
            return
            
        if response.status_code != 200:
            print(f"  [!] Server Error: {response.status_code}")
            return

        data = response.json()
        jobs = data.get('results', [])
        
        print(f"Successfully connected! Found {len(jobs)} jobs.")

        for job in jobs:
            try:
                # Clean up title
                title = job.get('title', '').replace('<strong>', '').replace('</strong>', '').strip()
                company = job.get('company', {}).get('display_name', 'Direct Hire')
                location = job.get('location', {}).get('display_name', 'Canada')
                link = job.get('redirect_url')

                if not link: continue

                category = get_category(title)
                
                job_data = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "tags": [category, "Verified"],
                    "job_type": "Full-Time"
                }

                supabase.table("jobs").upsert(job_data, on_conflict="link").execute()
                print(f"    [+] Saved: {title}")
                
            except Exception as e:
                continue

    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    scrape()
