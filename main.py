import re
from bs4 import BeautifulSoup
import time
import glob
import pymongo
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By


def downloadSearchPage(url, state):
    try:
        # update path
        prefs = {"download.default_directory": '********'}
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--start-fullscreen")
        driver = webdriver.Chrome(executable_path='chromedriver.exe', options=options)
        driver.implicitly_wait(10)
        driver.set_script_timeout(120)
        driver.set_page_load_timeout(10)

        driver.get(url)
        time.sleep(3)

        for i in range(0, 15):
            name = f"page_{state}_{i}.htm" if i > 9 else f"page_{state}_0{i}.htm"
            with open(name, "w", encoding='utf-8') as file:
                file.write(driver.page_source)
                time.sleep(10)

            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(5)

            if i < 14:
                next_page = driver.find_element(By.CSS_SELECTOR, 'a._1bfat5l.l1j9v1wn.dir.dir-ltr')
                next_page.click()
            time.sleep(5)

    except Exception as ex:
        print('error: ' + str(ex))


def loadSearchPage(page_list):
    combined = []
    try:
        for page in page_list:
            urls = []
            with open(page, "r", encoding='utf-8') as page_html:
                # Reading the file for each page
                content = page_html.read()
                # Create a beautifulsoup object for each page
                soup = BeautifulSoup(content, 'lxml')
                for i in range(0, 18):
                    urls.append(soup.select('div.cy5jw6o.dir.dir-ltr>a')[i].get('href'))
                combined.append(urls)
        return combined

    except Exception as ex:
        print('error: ' + str(ex))


def downloadPropertyPage(url_list):
    # update path
    prefs = {"download.default_directory": '**********'}
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--start-fullscreen")
    driver = webdriver.Chrome(executable_path='chromedriver.exe', options=options)
    driver.implicitly_wait(10)
    driver.set_script_timeout(120)
    driver.set_page_load_timeout(10)

    base = 'https://www.airbnb.com/'
    for i in range(0, 45):
        print(i)
        for j in range(0, 18):
            try:
                driver.get(base + url_list[i][j])
                # page_content = requests.get(base + url_list[i][j], headers=headers)
                time.sleep(10)

                if i < 15:
                    name = f"abb_CA_{i}_{j}.htm"
                elif i < 30:
                    name = f"abb_OR_{i}_{j}.htm"
                else:
                    name = f"abb_WA_{i}_{j}.htm"
                with open(name, "w", encoding='utf-8') as file:
                    file.write(driver.page_source)
                    time.sleep(5)

            except Exception as ex:
                print('error: ' + str(ex))


def change_format(bs_object):
    return re.sub(' +', ' ', bs_object.replace('\n', ''))


def loadPropertyPage(abb_page_list):
    obj = []
    for page in abb_page_list:
        with open(page, "r", encoding='utf-8') as page_html:
            # Reading the file for each page
            content = page_html.read()
            # Create a beautifulsoup object for each page
            soup = BeautifulSoup(content, 'lxml')
            page_no = re.sub(r".+?([\d]{1,2})(\_.+)", "\\1", page)
            state = re.sub(r".+?([A-Z][A-Z]).+", "\\1", page)

            name = soup.select_one('div._b8stb0>span>h1').text
            ratings = soup.select_one('span._17p6nbba')
            reviews = soup.select_one('span._s65ijh7')
            superhost = soup.select_one('span._1mhorg9')
            address = soup.select_one('span._9xiloll').text

            # use API to get latitude and longitude
            url_head = 'http://api.positionstack.com/v1/forward?'
            access_key = '*****************'
            query = change_format(address).strip()

            loc_api = url_head + 'access_key=' + access_key + '&' + 'query=' + query + '&limit=1'

            response = requests.get(loc_api)

            if response.status_code == 200:
                data = response.json()

                if len(data['data'][0]) == 0:
                    print('API failed')

                else:

                    latitude = data['data'][0]['latitude']
                    longitude = data['data'][0]['longitude']
                    geolocation = '(' + str(latitude) + ',' + str(longitude) + ')'

            price = soup.select_one('span._14y1gc>span.a8jt5op')
            price_formatted = re.sub(r"\\xa0", " ", price.text) if price else ''
            og_price = re.search(r"\boriginally\b", price_formatted)

            basics = soup.select_one('ol.lgx66tx.dir.dir-ltr')
            basics_list = []
            for basic in basics:
                x = re.sub(r".*?(\d+) ([a-zA-Z]+).*", "\\1 \\2", basic.text)
                basics_list.append(x)

            highlights = soup.select('div._1qsawv5')
            highlights_list = []
            for highlight in highlights:
                highlights_list.append(highlight.text)

            rooms = soup.select('div._muswv4')
            rooms_list = []
            for room in rooms:
                key_room = room.select_one('div._1auxwog').text
                value_room = room.select_one('div._1a5glfg').text
                room_obj = {
                    key_room: value_room
                }
                rooms_list.append(dict(room_obj))

            amenities = soup.select_one('div._1byskwn')
            amenities_list = []
            for amenity in amenities:
                amenities_list.append(amenity.select_one('div>div>div').text)

            services = soup.select('div._a3qxec')
            service_list = []
            for service in services:
                key_service = service.select_one('div._y1ba89').text
                value_service = service.select_one('span._4oybiu').text
                service_obj = {
                    key_service: value_service
                }
                service_list.append(dict(service_obj))

            abb_property = {
                'Page': page_no,
                'Name': name,
                'Ratings': re.sub(r"(\d.+?) .*", "\\1", ratings.text) if ratings else '',
                'Reviews': re.sub(r"(\d+) ([a-zA-Z]+)", "\\1", reviews.text) if reviews else '',
                'Superhost': superhost.text if superhost else '',
                'Discounted Price': re.sub(r"(\$\d{3,4}).*", "\\1", price_formatted),
                'Original Price': re.sub(r".+?(\$\d{3,4})", "\\1", price_formatted) if og_price else '',
                'Address': address,
                'geolocation': geolocation,
                'State': state,
                'Basics': basics_list,
                'Highlights': highlights_list,
                'Rooms': rooms_list,
                'Amenities': amenities_list,
                'Service Ratings': service_list
            }
        obj.append(dict(abb_property))
    return obj


def addToDB(data):
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")

    if "final_project" in myclient.list_database_names():
        myclient.drop_database("final_project")

    mydb = myclient["final_project"]

    if "airbnb" in mydb.list_collection_names():
        mydb.drop_collection("airbnb")

    collection = mydb["airbnb"]

    collection.insert_many(data)

    # creating index on the data
    collection.create_index("Ratings")
    collection.create_index("Superhost")
    collection.create_index([("Ratings", 1), ("Superhost", 1)], name="rating_superhost")


if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
    }

    # AirBnB search page download
    abb_search_CA = 'https://www.airbnb.com/s/California--United-States/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&price_filter_input_type=0&price_filter_num_nights=5&query=California%2C%20United%20States&place_id=ChIJPV4oX_65j4ARVW8IJ6IJUYs&date_picker_type=calendar&checkin=2023-03-23&checkout=2023-03-26&adults=2&source=structured_search_input_header&search_type=autocomplete_click'
    abb_search_WA = 'https://www.airbnb.com/s/Washington--United-States/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&price_filter_input_type=0&price_filter_num_nights=5&channel=EXPLORE&query=Washington%2C%20United%20States&place_id=ChIJ-bDD5__lhVQRuvNfbGh4QpQ&date_picker_type=calendar&checkin=2023-03-23&checkout=2023-03-26&adults=2&source=structured_search_input_header&search_type=autocomplete_click'
    abb_search_OR = 'https://www.airbnb.com/s/Oregon--United-States/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&price_filter_input_type=0&price_filter_num_nights=3&channel=EXPLORE&date_picker_type=calendar&checkin=2023-03-23&checkout=2023-03-26&adults=2&source=structured_search_input_header&search_type=autocomplete_click&query=Oregon%2C%20United%20States&place_id=ChIJVWqfm3xuk1QRdrgLettlTH0'
    downloadSearchPage(abb_search_CA, 'CA')
    downloadSearchPage(abb_search_WA, 'WA')
    downloadSearchPage(abb_search_OR, 'OR')
    #
    # # iterating through downloaded search pages to get url of individual property
    abb_search_pages = glob.glob('page*')
    abb_urls = loadSearchPage(abb_search_pages)
    #
    # # downloading page for each property
    downloadPropertyPage(abb_urls)
    #
    # # iterating over all the properties and fetching the values
    abb_prop_pages = glob.glob('abb*')
    final_list = loadPropertyPage(abb_prop_pages)

    # # storing the data in mongoDB
    addToDB(final_list)

