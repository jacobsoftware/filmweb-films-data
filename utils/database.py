import sqlite3
import os

CREATE_HREF_TABLE = 'CREATE TABLE IF NOT EXISTS href_table( itemID INTEGER PRIMARY KEY, film_title TEXT, film_url TEXT,year_production INTEGER)'
INSERT_INTO_HREF_TABLE = 'INSERT INTO href_table (film_title, film_url, year_production) VALUES (?,?,?)'
READ_HREFS = f'SELECT film_url FROM href_table'


CREATE_HREF_TABLE = '''CREATE TABLE IF NOT EXISTS film_data( itemID INTEGER PRIMARY KEY, 
                    film_title TEXT, 
                    film_title_eng TEXT, 
                    year_production INTEGER, 
                    director TEXT, 
                    writer TEXT,
                    studio TEXT, 
                    film_genre TEXT,
                    country_production TEXT,
                    duration INTEGER, 
                    actors TEXT,
                    rating REAL, 
                    votes INTEGER,
                    date_of_scrape TEXT)'''


INSERT_INTO_HREF_TABLE = '''INSERT INTO film_data (film_title, film_title_eng, year_production, 
                            director, writer, studio, film_genre, country_production, duration, actors, 
                            rating, votes, date_of_scrape) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)'''

def save_data(list: list,
              table_create: str,
              table_insert: str) -> None:

    connection = sqlite3.connect(os.path.join(os.path.dirname(__file__),"filmweb_db.db"))
    cursor = connection.cursor()
    
    sqlQueryCreateTable = table_create
    cursor.execute(sqlQueryCreateTable)

    sqlQueryInsertInto = table_insert
    cursor.executemany(sqlQueryInsertInto,list)
    connection.commit()
    connection.close()


def load_data(table_read: str) -> None:
    
    connection = sqlite3.connect(os.path.join(os.path.dirname(__file__),"filmweb_db.db"))
    cursor = connection.cursor()
    sqlQueryReadTable= table_read
    cursor.execute(sqlQueryReadTable)
    items = cursor.fetchall()
    return items




if __name__ == '__main__':
    sql = 'SELECT film_url FROM href_table WHERE film_url LIKE "%Logan%";'
    href = load_data(sql)
    print(href)