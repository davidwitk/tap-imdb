#! python3
# get_imdb_top_250.py - Downloads information on the 250 movies on IMDb.

import requests
import os
import bs4
import re
import datetime
import json
import singer
import hashlib
import logging

def get_imdb_top_250():
    url = 'https://www.imdb.com/chart/top/' 
    headers = {"Accept-Language": "en-US,en;q=0.5"}  # to get the movie titles in English language

    res = requests.get(url, headers=headers)
    res.raise_for_status()

    return res


def sync_imdb_top_250():
    
    res = get_imdb_top_250()

    movies = []
    extracted_at = datetime.datetime.now().isoformat()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')

    for movie in soup.select('div[class="lister"] tr'):
        if movie.select('td a') == []:
            continue
        title = movie.select('td[class="titleColumn"] a')[0].string
        year = int(movie.select('td[class="titleColumn"] span[class="secondaryInfo"]')[0].string.replace('(','').replace(')',''))
        rank = int(movie.select('td[class="titleColumn"]')[0].contents[0].strip().replace('.', ''))
        rating = float(movie.select('td[class="ratingColumn imdbRating"] strong')[0].string)
        rating_count = int(re.findall(r'\d+', movie.select('td[class="ratingColumn imdbRating"] strong')[0]['title'].replace(',','').replace('.',''))[1])
        link = 'https://imdb.com' + movie.select('td[class="titleColumn"] a')[0]['href']
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
