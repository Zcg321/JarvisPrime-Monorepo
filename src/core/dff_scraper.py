import requests
from bs4 import BeautifulSoup
from core.logger import log_event

# Scrape projections CSV from Daily Fantasy Fuel
def scrape_dff_csv():
    log_event("DFF Scraper", "Starting CSV scrape from Daily Fantasy Fuel...")
    try:
        url = "https://www.dailyfantasyfuel.com/nba/projections/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Attempt to find the CSV link
        csv_link = None
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and 'projections.csv' in href:
                csv_link = href if href.startswith('http') else f"https://www.dailyfantasyfuel.com{href}"
                break

        if csv_link:
            csv_data = requests.get(csv_link)
            if csv_data.status_code == 200:
                with open('projections.csv', 'wb') as file:
                    file.write(csv_data.content)
                log_event("DFF Scraper", "CSV downloaded successfully!")
            else:
                log_event("DFF Scraper", f"CSV request failed with status code: {csv_data.status_code}")
        else:
            log_event("DFF Scraper", "CSV link not found on the page.")

    except Exception as e:
        log_event("DFF Scraper", f"Scrape failed: {e}")
