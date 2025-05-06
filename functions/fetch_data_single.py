import requests
import logging
from bs4 import BeautifulSoup
import re
import json
def get_provider(url):
    payload = {}
    headers = {}

    response = requests.get(url, headers=headers, data=payload) # or requests.post() based on your api
    logging.info(f"status: {response.status_code} for url {url}")
    response.raise_for_status()
    response_data = response.text
    extracted_data = extract_data(response_data)
    return extracted_data

def extract_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find('script', string=re.compile(r'window\[\'__PAGE_CONTEXT_QUERY_STATE__\'\]'))
    json_data = re.finditer(r'window\[\'__PAGE_CONTEXT_QUERY_STATE__\'\] = {(.*?)};', script_tag.text)
    for match in json_data:
        data = match.group(1)
        data = "{" + data + "}"
        data = json.loads(data.replace('undefined','null'))
        data = data["src\u002Fcontainers\u002Fpages\u002Fhealth\u002Fdoctors\u002Fprofile\u002Fprofile.js"]["data"]["context"]["doctor"]
        return data