import time
import os
import pprint
from lxml import html
import asyncio
from datetime import datetime
from urllib import parse

import httpx
import aiohttp
from playwright.sync_api import sync_playwright
from requests_html import AsyncHTMLSession

from utils.json_files import load_json
from utils.database import *

COOKIES = load_json(os.path.join(os.path.dirname(__file__), 'keys.json'))
BASE_URL = 'https://www.filmweb.pl'
HEADERS = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

def find_hrefs(url: str,
                       start_year: int,
                       end_year: int,
                       how_many_films = 500) -> None:
    
    with sync_playwright() as p:

        browser = p.webkit.launch(headless=True)
        context = browser.new_context(
            user_agent= 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        context.add_cookies(COOKIES['Cookies'])
        page = context.new_page()
        page.goto(url)

        time.sleep(1.5)
        if page.query_selector('xpath=//div[@class="ws__wrapper isStarting"]'):
            time.sleep(2)
            page.click('xpath=//div[@class="ws__wrapper isStarting"]/div/div/button')
        
        
        for i in range(start_year-end_year+1):
            url = f'https://www.filmweb.pl/search#/films?startYear={start_year-i}&endYear={start_year-i}'
            page.goto(url)
            page.reload()
            length = 0
            list_of_data = []
            while length < how_many_films:
                page.keyboard.press('PageDown')
                #page.mouse.wheel(0,15000)
                films = page.locator('xpath=//div[@class="sc-dxcDKg cIMyWa"]/div[@class="sc-dycYrt sc-hTUWRQ eTFmFX jHcnKJ"]/div/div/div/a').all()
                length = len(films)
                print(f'Found {length} films')

            for film in films:
                film_title = film.inner_text()
                film_url = film.get_attribute('href')
                year_production = start_year - i
                data = (film_title, film_url, year_production)
                list_of_data.append(data)

            print(list_of_data)
            save_data(list_of_data,CREATE_HREF_TABLE,INSERT_INTO_HREF_TABLE)
            print('End of page ', year_production)



def load_urls(select_table: str) -> list:
    href = load_data(select_table)   
    list_of_href = []
    for i in range(len(href)):
        list_of_href.append(BASE_URL+href[i][0])
    return list_of_href


def parse_html(results):
    list_of_data = []
    for html_text in results:
        try: tree = html.fromstring(html_text)
        except: continue
    # Cover section
        # Title
        film_cover_section = tree.xpath('//div[@class="filmCoverSection__titleDetails"]')[0]
        film_title = film_cover_section.xpath('//h1/text()')[0]
        # English version of title
        if film_cover_section.xpath('//div[@class="filmCoverSection__originalTitle"]'):
            film_title_eng = film_cover_section.xpath('//div[@class="filmCoverSection__originalTitle"]/text()')[0]
        else: film_title_eng = film_title
        # Year
        film_year = film_cover_section.xpath('//div[@class="filmCoverSection__year"]/text()')[0]
        # Duration
        if film_cover_section.xpath('//div[@class="filmCoverSection__duration"]'):
            film_duration = film_cover_section.xpath('//div[@class="filmCoverSection__duration"]/@data-duration')[0]
        else: film_duration = 0

    # Preview content
        if tree.xpath('//div[@class="page__container filmCoverSection__ratings afterPremiere"]'):
            film_preview__content = tree.xpath('//div[@class="page__container filmCoverSection__ratings afterPremiere"]')[0]
            # Rating and votes
            if film_preview__content.xpath('//div/div[@class="filmRating__rate"]/span[1]'):
                film_rating = film_preview__content.xpath('//div/div[@class="filmRating__rate"]/span[1]/text()')[0]
                film_rating = film_rating.replace(',','.')
                film_votes = film_preview__content.xpath('//div/div/span[2]/text()')[0]
                film_votes = film_votes.replace(' ','')
            else:
                film_rating = 0
                film_votes = 0
        else:
            film_rating = 0
            film_votes = 0 

    # Poster section
        film_poster_section = tree.xpath('//div[@class="filmPosterSection__info filmInfo"]')[0]
        # Director
        directors = film_poster_section.xpath('//div[@class="filmInfo__info cloneToCast cloneToOtherInfo"][1]/a/span/text()')
        film_director = loop_items(directors)
        # Writer
        if film_poster_section.xpath('//div[@class="filmInfo__info cloneToCast cloneToOtherInfo"][2]/a/span'):
            writers = film_poster_section.xpath('//div[@class="filmInfo__info cloneToCast cloneToOtherInfo"][2]/a/span/text()')
            film_writer = loop_items(writers)
        else: film_writer = None
        # Genre
        genres = film_poster_section.xpath('//div[@itemprop="genre"]/span/a/span/text()')
        film_genre = loop_items(genres)
        # Country
        countries = film_poster_section.xpath('//div[@class="filmInfo__info filmInfo__info--productionCountry"]/span/a/span/text()')
        film_country_production = loop_items(countries)

        # Actors
        actors = tree.xpath('//div[@class="Crs crs crs--limited crs--roundedNavigation"]/div//a/h3/text()')
        film_actors = loop_items(actors)

        # Studio
        if tree.xpath('//div[@class="filmOtherInfoSection__content"]//div[@class="filmInfo__group filmInfo__group--studios"]/div[@class="filmInfo__info"]'):
            studios = tree.xpath('//div[@class="filmOtherInfoSection__content"]//div[@class="filmInfo__group filmInfo__group--studios"]/div[@class="filmInfo__info"]/text()')

            film_studio = ''
            garbage_removed = []
            for index in range(len(studios)):
                if studios[index] == ' ' or studios[index] == ' / ': pass
                else:
                    work_on_string = str(studios[index])
                    work_on_string = work_on_string.rstrip()
                    if ' /' in work_on_string: work_on_string = work_on_string.replace(' /','')
                    if work_on_string[0] == ' ': work_on_string = work_on_string[1:]
                    garbage_removed.append(work_on_string)

                    if index<len(studios)-1: film_studio = f'{film_studio}{work_on_string},'
                    else: film_studio = f'{film_studio}{work_on_string}'
           
        else: film_studio = None

        current_date = datetime.today().strftime('%d-%m-%Y')
        data = [film_title, film_title_eng, film_year, film_director, film_writer, film_studio, film_genre, 
                film_country_production, film_duration, film_actors, film_rating, film_votes, current_date]
        list_of_data.append(data)
        #pprint.pprint(data)
    save_data(list_of_data,CREATE_HREF_TABLE,INSERT_INTO_HREF_TABLE)
        
def loop_items(items: list) -> str:
    extracted_data = ''
    for index in range(len(items)):
        if index<len(items)-1:
            extracted_data = extracted_data + items[index] + ','
        else: extracted_data = extracted_data + items[index]
    return extracted_data


async def get_episode(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print('URL:',url,' Status code:',response.status_code)
        return response.text
 
async def go(urls):
    tasks = [get_episode(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results


if __name__ == '__main__':

    #find_hrefs('https://www.filmweb.pl/films/search',2024,2024)
    urlx = load_urls(READ_HREFS)
    print(len(urlx))
    x = 27999
    while x < len(urlx):

        get_href = f'SELECT film_url FROM href_table WHERE itemID > {x} AND itemID <= {x+500}'
        urls = load_urls(get_href)
        results = []
        results = asyncio.run(go(urls))
        parse_html(results)
        x = x+500
        print('pause')
        time.sleep(15)