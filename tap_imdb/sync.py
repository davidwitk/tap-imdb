import bs4
import datetime
import singer
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def get_imdb_top_250():
    
    # Set Chrome webdriver
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)  
    
    # Request page
    driver.get('https://www.imdb.com/chart/top/')

    # Select detailed view (this is why we actually use Selenium now)
    driver.find_element(By.ID, 'list-view-option-detailed').click()

    # Scroll to bottom of the page due to dynamic page loading
    SCROLL_PAUSE_TIME = 0.5
    last_height = driver.execute_script("return document.body.scrollHeight") # Get scroll height
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll down to bottom
        time.sleep(SCROLL_PAUSE_TIME) # Wait to load page
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

        title = movie.find(class_='ipc-title__text').get_text().split('.')[1].strip()
        year = movie.find_all(class_='sc-14dd939d-6')[0].get_text()
        rank = movie.find(class_='ipc-title__text').get_text().split('.')[0]
        rating = movie.find("span", class_="ipc-rating-star").get_text()
        rating_count = movie.find("div", class_="sc-86b9674b-0").get_text().replace('Votes','').replace(',','').replace('.','')
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
