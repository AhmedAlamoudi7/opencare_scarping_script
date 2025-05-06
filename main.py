import os
import logging
import time
from functions.search import SitemapFetcher
from functions.mpc_formatter import JSONFormatter
from functions.fetch_data_bulk import fetch_all_data
import argparse

# Configure logging
def setup_logging(base_folder):
    global error_logger, success_logger

    logs_folder = os.path.join(base_folder, "logs")
    os.makedirs(logs_folder, exist_ok=True)
    success_log_path = os.path.join(logs_folder, "success.log")
    error_log_path = os.path.join(logs_folder, "fail.log")

    # Error Logger
    error_logger = logging.getLogger("error_logger")
    error_logger.handlers.clear()
    error_handler = logging.FileHandler(error_log_path)
    error_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    error_handler.setFormatter(error_formatter)
    error_logger.addHandler(error_handler)
    error_logger.setLevel(logging.ERROR)

    # Success Logger
    success_logger = logging.getLogger("success_logger")
    success_logger.handlers.clear()
    success_handler = logging.FileHandler(success_log_path)
    success_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    success_handler.setFormatter(success_formatter)
    success_logger.addHandler(success_handler)
    success_logger.setLevel(logging.INFO)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch Doctors From Zocdoc Website.')
    parser.add_argument('--input_urls', '-i', type=str, help='File with List of Urls To scrape')
    parser.add_argument('--output_dir', '-o', type=str, required=True, help='Directory to save the output')
    parser.add_argument('--format_only', '-f', action='store_true', help='Only format the output directory')
    parser.add_argument('--threads', '-t', type=int, default=10, help='No. of concurrent processes to run (default: 5)')
    
    args = parser.parse_args()

    urls_file = args.input_urls
    output_directory = args.output_dir

    setup_logging(output_directory)
    
    if not args.format_only:
        # First Step : if no existing urls to extract, go fetch all urls either from sitemap or website search page
        if not urls_file:
            fetcher = SitemapFetcher(output_dir=output_directory)
            fetcher.fetch_and_extract_sitemaps()
            urls_file = os.path.join(output_directory, "all_urls.txt")

        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        start_time = time.time()
        # Second Step : get all urls and fetch their html & json data and save it to output_dir/raw_data folder
        fetch_all_data(urls, os.path.join(output_directory), args.threads)
        elapsed_time = time.time() - start_time
        success_logger.info(f"All URLs scraped successfully in {elapsed_time:.2f} seconds.")

    # # Third Step : format the raw data to a structured format and save it to output_dir/formatted folder
    formatter = JSONFormatter(output_directory)
    formatter.process_directory()