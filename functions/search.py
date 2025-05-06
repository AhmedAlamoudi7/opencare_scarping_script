# import os
# import requests
# from bs4 import BeautifulSoup

# class SitemapFetcher:
#     def __init__(self, output_dir):
#         self.output_dir = output_dir
#         self.sitemaps_file = os.path.join(output_dir, "sitemaps.txt")
#         self.all_urls_file = os.path.join(output_dir, "all_urls.txt")

#     def fetch_and_extract_sitemaps(self):
#         # Fetch sitemaps logic here (if applicable)
#         print("Fetching sitemaps...")
#         # Example: Fetch sitemaps and save them to self.sitemaps_file
#         with open(self.sitemaps_file, "w") as f:
#             f.write("https://example.com/sitemap.xml\n")

#         # Extract URLs from sitemaps
#         urls = []
#         with open(self.sitemaps_file, "r") as f:
#             for line in f:
#                 sitemap_url = line.strip()
#                 response = requests.get(sitemap_url)
#                 soup = BeautifulSoup(response.content, "xml")
#                 locs = soup.find_all("loc")
#                 urls.extend([loc.text for loc in locs])

#         # Save all extracted URLs to a file
#         with open(self.all_urls_file, "w") as f:
#             f.write("\n".join(urls))
#         print(f"Extracted {len(urls)} URLs and saved to {self.all_urls_file}")



import os
import logging
import requests
import xml.etree.ElementTree as ET
import argparse
import json

class SitemapFetcher:
    def __init__(self, sitemap_types, output_dir="output", max_retries=3):
        self.sitemap_types = sitemap_types
        self.base_url = "https://www.opencare.com"
        self.output_dir = output_dir
        self.progress_file = os.path.join(output_dir, "progress.json")
        self.max_retries = max_retries
        self.progress = self._load_progress()
        self.log_file = os.path.join(output_dir, "sitemap_fetcher.log")
        
        # Set output file name based on type selection
        if len(sitemap_types) == 2:
            self.output_file = os.path.join(output_dir, "all_urls.txt")
        elif "doctor" in sitemap_types:
            self.output_file = os.path.join(output_dir, "providers_urls.txt")
        elif "clinic" in sitemap_types:
            self.output_file = os.path.join(output_dir, "practices_urls.txt")
        
        os.makedirs(output_dir, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(), logging.FileHandler(self.log_file)],
        )
    
    def _load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r", encoding="utf-8") as file:
                return json.load(file)
        return {"fetched": [], "failed": []}

    def _save_progress(self):
        with open(self.progress_file, "w", encoding="utf-8") as file:
            json.dump(self.progress, file, indent=4)
    
    def fetch_sitemap(self, sitemap_type):
        index = 0
        urls = []
        
        while True:
            sitemap_url = f"{self.base_url}/oc-sitemap-{sitemap_type}-{index}.xml"
            
            response = requests.get(sitemap_url)
            if response.status_code != 200:
                logging.info(f"No more sitemaps found for {sitemap_type} at index {index}. Stopping.")
                break

            if "AccessDenied" in response.text:
                logging.warning(f"Access Denied encountered at index {index}. Stopping.")
                break

            logging.info(f"Fetching URLs from: {sitemap_url}")
            
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError:
                logging.error(f"Failed to parse XML at index {index}. Skipping.")
                logging.error(f"Response Content:\n{response.text}")
                break

            for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                urls.append(loc.text)
            
            index += 1
        
        return urls
    
    def fetch_and_save_sitemaps(self):
        all_urls = []
        
        for sitemap_type in self.sitemap_types:
            logging.info(f"Fetching {sitemap_type} sitemaps...")
            
            all_urls.extend(self.fetch_sitemap(sitemap_type))
        
        with open(self.output_file, "w", encoding="utf-8") as f:
            for url in all_urls:
                f.write(url + "\n")
        
        logging.info(f"Total {len(all_urls)} URLs saved to {self.output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch URLs from OpenCare sitemaps.\n\n"
                    "python search.py --type doctor (Fetch providers only)\n"
                    "python search.py --type clinic (Fetch practices only)\n"
                    "python search.py --type both (Fetch both, default)\n",
        formatter_class=argparse.RawTextHelpFormatter
    )
    # parser.add_argument("--type", choices=["doctor", "clinic", "both"], default="both", help="Choose sitemap type: 'doctors' for providers, 'clinics' for practices, or 'both' for all.")
    parser.add_argument("--type", choices=["doctor"], default="both", help="Choose sitemap type: 'doctors' for providers, 'clinics' for practices, or 'both' for all.")

    args = parser.parse_args()

    # sitemap_types = ["doctor", "clinic"] if args.type == "both" else [args.type]
    sitemap_types = ["doctor"] 

    fetcher = SitemapFetcher(sitemap_types)
    fetcher.fetch_and_save_sitemaps()
