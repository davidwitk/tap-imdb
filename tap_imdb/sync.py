import requests
import bs4
import datetime
import singer
import hashlib
import json

def get_imdb_top_250():
    url = 'https://www.imdb.com/chart/top/' 
    headers = {
        "Accept-Language": "en-US,en;q=0.5", # to get the movie titles in English language
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }  

    res = requests.get(url, headers=headers)
    res.raise_for_status()

    return res


def sync_imdb_top_250():
    
    res = get_imdb_top_250()
    movies_soup = bs4.BeautifulSoup(res.text, 'html.parser').find(id='__NEXT_DATA__')
    movies_json_raw = json.loads(movies_soup.get_text()) 
    movies_json = movies_json_raw["props"]["pageProps"]["pageData"]["chartTitles"]["edges"]
    extracted_at = datetime.datetime.now().isoformat()

    movies = []
    for movie in movies_json: 
        title = movie["node"]["titleText"]["text"]
        id = movie["node"]["id"]
        year = movie["node"]["releaseYear"]["year"]
        rank = movie["currentRank"]
        rating = str(movie["node"]["ratingsSummary"]["aggregateRating"])
        rating_count = movie["node"]["ratingsSummary"]["voteCount"]
        link = f"https://imdb.com/title/{id}/"  
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
