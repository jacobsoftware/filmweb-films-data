from scraper import *



def get_data():
    list_of_urls = load_urls(READ_HREFS)
    id_of_hrefs_table = 0
    while x < len(list_of_urls):

        get_href = f'SELECT film_url FROM href_table WHERE itemID > {x} AND itemID <= {x+500} ORDER BY year_production DESC'
        urls = load_urls(get_href)
        results = []
        results = asyncio.run(go(urls))
        parse_html(results)
        x = x+500
        print('pause')
        time.sleep(15)


def main():
    pass


if __name__ == '__main__':
    load_data('href_table')