import time

import pandas as pd
import requests
import numpy as np
import os
import random
import logging
from tqdm import tqdm
import glob
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO)
logger_url = logging.getLogger("download_image")
file_logger = logging.FileHandler(os.path.join(BASE_DIR, 'log/download_image.log'), mode='a')
file_logger.setFormatter(logging.Formatter('[%(asctime)s]:[%(levelname)s]:%(message)s'))
logger_url.setLevel(logging.INFO)
logger_url.addHandler(file_logger)

def download_image(logger=logger_url):
    logger.info('#'*100)
    arr_res_details_file = glob.glob('data/details/*.csv')
    for file in arr_res_details_file:
        logger.info('-' * 50 + f'Crawling file {file}')
        df = pd.read_csv(file)
        for idx, row in df.iterrows():
            logger.info('+'*20)
            if idx >5:
                break
            company = row['Company']
            arr_urL_img = row['List image']
            arr_urL_img = arr_urL_img.replace("\'", '').replace('[', '').replace(']', '').split(',')
            logger.info(f'Crawling restaurant: {company}')
            logger.info(f'Total image have: {len(arr_urL_img)}')
            path_dir = f'data/images/{company}'
            try:
                os.mkdir(path_dir)
                print(f'Create folder {path_dir}')
            except FileExistsError:
                print(f'{path_dir} is exist')

            image_crawl = glob.glob(f'{path_dir}/*.png')
            count_exist = 0
            count_downloaded = 0
            count_error = 0
            begin = datetime.now()
            for idu in tqdm(range(len(arr_urL_img)), desc="Download image"):
                url = arr_urL_img[idu]
                index_remove = url.find('=')
                url = url[:index_remove]

                # download image
                path = path_dir + f'/{company}_{idu}.png'
                if path in image_crawl:
                    print(f'{path} is downloaded')
                    count_exist +=1
                    continue
                try:
                    r = requests.get(url, headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"
                    })
                    if r.status_code == 200:
                        with open(path, 'wb') as f:
                            for chunk in r.iter_content(1024):
                                f.write(chunk)
                    count_downloaded+=1
                except Exception as e:
                    print(e)
                    if 'http' not in url:
                        print('url format error')
                    else:
                        print(f'{url} is error')
                    time.sleep(3)
                    count_error+=1
                time.sleep(random.randint(2, 5))
            logger.info(f'count_exist: {count_exist}')
            logger.info(f'count_downloaded: {count_downloaded}')
            logger.info(f'count_error: {count_error}')
            end = datetime.now()
            print(f'Time download: {(end-begin)/60}')
            print()
if __name__ =='__main__':
    logger_url.info('abc')
    download_image()



