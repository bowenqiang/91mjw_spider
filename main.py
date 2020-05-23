import requests
from bs4 import BeautifulSoup
import re
from pymongo import MongoClient
import time
import logging
import multiprocessing
from multiprocessing import Pool

PROXY_POOL_URL = 'http://192.168.123.99:5555/random'

logging.basicConfig(
    # 日志级别,logging.DEBUG,logging.ERROR
    level = logging.INFO,  
    # 日志格式
    # 时间、代码所在文件名、代码行号、日志级别名字、日志信息
    format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    # 打印日志的时间
    datefmt = '%a, %Y-%m-%d %H:%M:%S',
    # 日志文件存放的目录（目录必须存在）及日志文件名
    filename = '/home/wenqiang/logs/91mjw.log',
    # 打开日志文件的方式
    filemode = 'w'
)

def get_random_proxy():
    text = None
    while(not text):
        try:
            text = requests.get(PROXY_POOL_URL).text.strip()
        except:
            text = None
            time.sleep(1)

    return text

def main(url):
    print(url)
    html = request_91mjw(url)

    try:
        soup = BeautifulSoup(html, 'lxml')
    except:
        soup = None
    
    data = extract_data(soup, url)
    if data:
        save_to_db(data)
        logging.info('save page： ' + url + ' successfully')
    else:
        logging.warning('page: ' + url + ' might not exist')
    time.sleep(5)


def request_91mjw(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'
    }
    proxy = get_random_proxy()
    proxies = {'http': 'http://' + proxy}
    try:
        response = requests.get(url,headers=headers,proxies=proxies)
        if response.status_code == 200:
            return response.text
    except response.RequestException:
        return None

def extract_data(soup, url):
    if not soup:
        return None
    # redirect to homepage
    isHomepage = soup and soup.find(class_='m-movies')
    if isHomepage:
        return None
    # redirect to 404 page
    is404 = soup and soup.find(class_='error404')
    if is404:
        return None

    movie_title = (soup.find(class_='article-title') and soup.find(class_='article-title').find('a').string) or 'None'

    movie_info = soup and soup.find(class_='video_info')

    pattern = re.compile(r'类型:')
    movie_category = (movie_info and movie_info.find('strong', text=pattern) and movie_info.find('strong', text=pattern).next_sibling) or 'None'

    pattern = re.compile(r'IMDb编码:')
    movie_imdb = (movie_info and movie_info.find('strong', text=pattern) and movie_info.find('strong', text=pattern).next_sibling) or 'None'

    pattern = re.compile(r'又名:')
    movie_alternative_title = (movie_info and movie_info.find('strong', text=pattern) and movie_info.find('strong', text=pattern).next_sibling) or 'None'

    download_list = soup and soup.find(id='download-list') and soup.find(id='download-list').find_all('li') or []
    episode = []
    for item in download_list:
        item_name = item.get('title', 'No title')
        pattern = re.compile(r'电驴下载')
        item_emule_link = (item.find('a', text=pattern) and item.find('a', text=pattern).get('href', 'No download link')) or 'None'
        pattern = re.compile(r'磁力下载')
        item_megnet_link = (item.find('a', text=pattern) and item.find('a', text=pattern).get('href', 'No download link')) or 'None'
        episode.append({
            "name": item_name,
            "emule_link": item_emule_link,
            "megnet_link": item_megnet_link,
        })
    if not len(episode):
        return None

    movie_data = {
        "title":movie_title,
        "category":movie_category,
        "imdb":movie_imdb,
        "alternative_title": movie_alternative_title,
        "url": url,
        "episode": episode,
        }
    return movie_data

def save_to_db(data):
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['91mjw']
        db.movies.insert_one(data)
    except:
        logging.error("save to db failed")

if __name__ == "__main__":
    logging.info('start')

    # multiporcessing
    urls = []
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    for i in range(0, 6000):
        url = 'https://91mjw.com/video/' + str(i) + '.htm'
        urls.append(url)
    pool.map(main, urls)
    pool.close()
    pool.join()
    print('done')
    logging.info('done')