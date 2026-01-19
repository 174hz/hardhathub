import requests
import os
from supabase import create_client

# 1. Setup Supabase
# These use your existing GitHub Secrets for safety
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# 2. ADZUNA API CREDENTIALS (Integrated)
ADZUNA_APP_ID = "767ae6dd"
ADZUNA_APP_KEY = "70924a39e11a69130b6042d703ed2266"

def get_category(title):
    """Categorizes jobs based on functional tasks in the title"""
    title = title.lower()
    if any(word in title for word in ["forklift", "operator", "machine"]): 
        return "Machinery & Forklift"
    if any(word in title for word in ["picker", "packer", "order"]): 
        return "Picking & Packing"
    if any(word in title for word in ["loader", "unloader", "handler", "handballer"]): 
        return "Loading & Unloading"
    if any(word in title for word in ["stock", "inventory", "receiving", "receiver"]): 
        return "Inventory & Stocking"
    return "Moving & Logistics"

def scrape():
    print("Initiating National Logistics Scan via Adzuna API...")
    
    # We are searching for 'warehouse' in Canada ('ca')
    # Fetching 50 results to fill the board quickly
    api_url = f"https://api.adzuna.com/v1/api/jobs/ca/search/1?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}&results_per_page=50&what=warehouse%20laborer"
    
    try:
        response = requests.get(api_url, timeout=15)
        
        if response.status_code != 200:
            print(f"  [!] API Error: Received status code {response.status_code}")
            return

        data = response.json()
        jobs = data.get('results', [])
        
        print(f"Detected {len(jobs)} live Canadian listings...")

        for job in jobs:
            try:
                # API titles often contain <strong> tags; this removes them
                raw_title = job.get('title', '')
                clean_title = raw_title.replace('<strong>', '').replace('</strong>', '').strip()
                
                company = job.get('company', {}).get('display_name', 'Direct Hire')
                location = job.get('location', {}).get('display_name', 'Canada')
                link = job.get('redirect_url')

                if not link: continue

                category = get_category(clean_title)
                
                job_entry = {
                    "title": clean_title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "tags": [category, "Verified"],
                    "job_type": "Full-Time"
                }

                # Save to Supabase (upsert avoids duplicates)
                supabase.table("jobs").upsert(job_entry, on_conflict="link").execute()
                print(f"    [+] Logged: {clean_title}")
                
            except Exception as e:
                continue

    except Exception as e:
        print(f"Scan interrupted: {e}")

if __name__ == "__main__":
    scrape()
