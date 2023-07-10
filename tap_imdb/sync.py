import bs4
import datetime
import singer
import hashlib
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import time

def get_imdb_top_250():
    
    # IMDb seems to expose the new page design randonmly based on an AB-Test. In some cases, the old page design
    # might still appear. In this case, we simply try again to get the new page design.
    i = 0
    while i < 10:     
        i += 1

        try: 
            logging.info('Setting Firefox driver.')
            
            # Set Firefox webdriver
            options = Options()
            options.add_argument("--headless")
            options.set_preference('intl.accept_languages', 'en-US, en')
            driver = webdriver.Firefox(options=options)

            # Request page
            logging.info(f'Requesting the website and trying to parse the HTML - attempt {i}.')
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

            break

        except Exception as e:
            logging.info('Oops! That was not the new page design. Try again...')

    return soup 

def sync_imdb_top_250():
    
    res = get_imdb_top_250()
    movies_soup = res.find_all(class_='ipc-metadata-list-summary-item')
    extracted_at = datetime.datetime.now().isoformat()

    movies = []
    for movie in movies_soup: 

        title = movie.find(class_='ipc-title__text').get_text().split('.', 1)[1].strip()
        year = movie.find_all(class_='sc-14dd939d-6')[0].get_text()
        rank = movie.find(class_='ipc-title__text').get_text().split('.', 1)[0]
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
