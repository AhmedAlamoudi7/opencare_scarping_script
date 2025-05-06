import os
import random
import time
import json
import re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
# Set headers to mimic a real browser request
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}

# ScrapeOps Proxy
scrapeops_api_key = ""
proxy_url = "https://proxy.scrapeops.io/v1/"

def process_url(url, output_directory):
    max_retries = 2
    retry_delay = 15
    os.makedirs(output_directory, exist_ok=True)

    # Extract ID from URL
    #for clinic 
    id_pattern = re.compile(r"-(\d+)[a-z]?/")
    match = id_pattern.search(url)
    provider_id = match.group(1) if match else None
    if not provider_id:
        print(f"Could not extract ID from URL: {url}")
        return False

    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1} of {max_retries}")
        time.sleep(random.uniform(7, 15))
        try:
            response = requests.get(
                url= url,
                headers=headers,
             )
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Save raw HTML content
            html_filename = re.sub(r"[^\w\-_\. ]", "_", url) + ".html"
            filepath = os.path.join(output_directory, "html_data", html_filename)
            with open(filepath, "w", encoding="utf-8") as html_file:
                html_file.write(soup.prettify())
            print(f"Raw HTML saved to '{filepath}'")

            # Fetch data from API using the extracted ID
            api_url = f"https://api.opencare.com/doctor?id={provider_id}"
            api_response = requests.get(api_url)
            api_data = api_response.json()

            # Save the extracted data to JSON
            json_filepath = os.path.join(output_directory, "raw_data", f"provider_{provider_id}.json")
            with open(json_filepath, "w", encoding="utf-8") as json_file:
                json.dump(api_data, json_file, ensure_ascii=False, indent=4)
            print(f"Data successfully saved to {json_filepath}")

            return True
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Skipping this URL.")
                return False


def fetch_all_data(urls, output_directory, max_threads=10):
    completed_urls = set()
    progress_file = os.path.join(output_directory, "progress.txt")

    # Load previously completed URLs
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            completed_urls = {line.strip() for line in f}
        print(f"Loaded {len(completed_urls)} completed URLs from {progress_file}.")
    else:
        print("No progress file found. Starting fresh.")

    remaining_urls = [url for url in urls if url not in completed_urls]
    print(f"Found {len(remaining_urls)} unprocessed URLs.")

    with tqdm(total=len(remaining_urls), desc="Processing URLs") as progress_bar:
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = []
            for url in remaining_urls:
                future = executor.submit(process_url, url, output_directory)
                futures.append((future, url))

            for future, url in futures:
                try:
                    success = future.result()
                    if success:
                        with open(progress_file, "a") as f:
                            f.write(f"{url}\n")
                        print(f"URL {url} successfully processed.")
                    else:
                        print(f"URL {url} failed. Skipping...")
                except Exception as e:
                    print(f"Error processing URL {url}: {e}")
                finally:
                    progress_bar.update(1)

    print("Processing complete.")