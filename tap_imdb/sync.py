import bs4
import datetime
import singer
import hashlib
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import time

def get_imdb_top_250():
    
    logging.info('Setting Chrome driver.')
    
    # Set Chrome webdriver
    chromedriver_autoinstaller.install() 
    options = Options()
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    # Request page
    logging.info(f'Requesting the website and parsing the HTML.')
    driver.get('https://www.imdb.com/chart/top/')

    # Select detailed view (this is why we actually use Selenium)
    driver.find_element(By.ID, 'list-view-option-detailed').click()

    # Scroll to bottom of the page due to dynamic page loading
    scroll_pause_time = 0.5
    last_height = driver.execute_script("return document.body.scrollHeight") # Get scroll height
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll down to bottom
        time.sleep(scroll_pause_time) # Wait to load page
        new_height = driver.execute_script("return document.body.scrollHeight") # Calculate new scroll height and compare with last scroll height
        if new_height == last_height:
            break
        last_height = new_height

    soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')

    driver.close()

    return soup 

def sync_imdb_top_250():
    
    res = get_imdb_top_250()
    movies_soup = res.find_all(class_='ipc-metadata-list-summary-item')
    extracted_at = datetime.datetime.now().isoformat()

    movies = []
    for movie in movies_soup: 

        title = movie.find(class_='ipc-title__text').get_text().split('.', 1)[1].strip()
        year = movie.find('span', class_='dli-title-metadata-item').text
        rank = movie.find(class_='ipc-title__text').get_text().split('.', 1)[0]
        rating = movie.find("span", class_="ipc-rating-star").get_text(strip=True).split('(', 1)[0]
        rating_count = movie.find('span', text='Votes').find_next_sibling(text=True).strip().replace(',','')
        link = 'https://imdb.com' + movie.select("a", class_='ipc-title-link-wrapper')[0]['href'].split('?')[0]
        id = hashlib.md5((title + extracted_at).encode('utf-8')).hexdigest() 

        data = {
            "id": id, 
            "title": title,
            "year": year,
            "rank": rank,
            "rating": rating,
            "rating_count": rating_count,
            "link": link,
            "extracted_at": extracted_at
        }

        movies.append(data)

    singer.write_schema(
        'imdb', 
        {'properties': {
            'id': {'type': 'string', 'key': True},
            'title': {'type': 'string'},
            "year": {"type": "integer"},
            "rank": {"type": "integer"},
            "rating": {"type": "string"},
            "rating_count": {"type": "integer"},
            "link": {"type": "string"},
            "extracted_at": {"type": "string"}
            }},
        ['id']
        )

    singer.write_records('imdb', movies)
