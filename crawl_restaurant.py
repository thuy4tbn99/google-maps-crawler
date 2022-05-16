import pandas as pd
import random
import time
from datetime import datetime
import json
import os
import glob

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

import logging
from tqdm import tqdm

from utils import delete_cache, remove_accents

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

logger_url = logging.getLogger("get_restaurant_url")
file_logger = logging.FileHandler(os.path.join(BASE_DIR, 'log/get_restaurant_url.log'), mode='a')
file_logger.setFormatter(logging.Formatter('[%(asctime)s]:[%(levelname)s]:%(message)s'))
logger_url.setLevel(logging.INFO)
logger_url.addHandler(file_logger)

logger_details = logging.getLogger("crawl_restaurant_details")
file_logger = logging.FileHandler(os.path.join(BASE_DIR, 'log/crawl_restaurant_details.log'), mode='a')
file_logger.setFormatter(logging.Formatter('[%(asctime)s]:[%(levelname)s]:%(message)s'))
logger_details.setLevel(logging.INFO)
logger_details.addHandler(file_logger)

# init
MINUTE_WAIT = 5


def initDriver():
    CHROMEDRIVER_PATH = './driver/chromedriver'
    WINDOW_SIZE = "1280,768"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-blink-features=AutomationControllered")
    chrome_options.add_experimental_option('useAutomationExtension', False)
    prefs = {"profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument('disable-infobars')
    chrome_options.add_argument('--log-level=3')
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                              options=chrome_options,
                              )
    return driver




# crawl with query search by town
def crawl_url(logger=logger_url):
    logger.info('#-------------------------------------------------')
    df = pd.read_csv('./data/DS_tinh_thanh.csv')
    df_hn = df[df['Tỉnh Thành Phố']=='Thành phố Hà Nội']
    list_district = ['Quận Ba Đình', 'Quận Hoàn Kiếm', 'Quận Tây Hồ', 'Quận Cầu Giấy','Quận Đống Đa',
                          'Quận Hai Bà Trưng','Quận Hoàng Mai', 'Quận Thanh Xuân','Quận Nam Từ Liêm',
                          'Quận Bắc Từ Liêm', 'Quận Hà Đông']
    df_hn_core = df_hn[df_hn['Quận Huyện'].isin(list_district)]
    arr_town = df_hn_core['Phường Xã'].tolist()

    driver = None
    for idx, town in enumerate(arr_town[22:]):
        print('driver: ', driver)
        
        if driver is None:
            driver = initDriver()
        # resolve Max retries exceeded with url
        if idx>0 and idx % 5==0:
            driver.quit()
            time.sleep(30)
            driver = initDriver()
        
        
        with open('data/crawled_town.txt', 'r') as f:
            arr_town_crawled = f.readlines()
            f.close()
            arr_town_crawled = [x.replace('\n', '') for x in arr_town_crawled]
        if town in arr_town_crawled:
            print(f'{town} is crawled')
            continue
        query_search = f'restaurant near {town}'
        logger.info(f'query_search: {remove_accents(query_search)}')
        try:
            crawl_restaurant(driver, query_search, town, logger=logger)
            with open('data/crawled_town.txt', 'a') as f:
                f.write(town+'\n')
                f.close()
        except Exception as e:
            print('here', e)
            driver.quit()

    return

def crawl_restaurant(driver, query_search, town, logger):
    begin = datetime.now()
    driver.get('https://maps.google.com/')
    time.sleep(3)
    inputSearchEle = driver.find_element_by_class_name('tactile-searchbox-input')
    inputSearchEle.send_keys(query_search)
    inputSearchEle.send_keys(Keys.ENTER)
    time.sleep(8)
    logger.info('Scrolling url ...')

    # scroll restaurant until end
    script_js = "function sleep(ms){return new Promise(resolve=>setTimeout(resolve,ms))};var el_list=document.getElementsByClassName('hfpxzc');var count=1;while(el_list.length<20||count>100){count+=1;el_list=document.getElementsByClassName('hfpxzc');el=el_list[el_list.length-1];el.scrollTop=el.scrollHeight;el.scrollIntoView();await sleep(1000);console.log(el_list.length);if(el_list.length==20){count=1};console.log('count:',count)}"
    driver.execute_script(script_js)

    arr_res_ele = driver.find_elements_by_class_name('hfpxzc')
    arr_link_res = [x.get_attribute('href') for x in arr_res_ele]

    all_link_res = []
    all_link_res.extend(arr_link_res)

    # scroll and goto next-page
    # get link restaurant
    while(True):
        try:
            driver.find_element_by_id('ppdPk-Ej1Yeb-LgbsSe-tJiF1e').click()
            time.sleep(5)
            driver.execute_script(script_js)
            arr_link_res = [x.get_attribute('href') for x in driver.find_elements_by_class_name('hfpxzc')]
            print(f'Got {len(arr_link_res)} links')
            # logger.info('Scrolling ...')
            all_link_res.extend(arr_link_res)
        except Exception as e:
            print('Finish scroll')
            break

    logger.info(f'all_link_restaurant: {len(all_link_res)}', )
    print(len(all_link_res), all_link_res[10])
    time.sleep(5)
    file_save = f'data/url/restaurant_{town}.txt'
    with open(file_save, 'w') as f:
        for link in all_link_res:
            f.write("%s\n" % link)
        f.close()

    end = datetime.now()
    time_run_minute = (end-begin)/60
    logger.info(f'Time run {remove_accents(town)}: {time_run_minute} minutes')
    logger.info(f'Save to {remove_accents(file_save)}')
    print(f'Time run {town}: ', (end-begin)/60, 'minutes')
    print()

    return

"""
@input: file contains list of restaurant urls
@output: .csv
"""
def crawl_restaurant_details(filename, driver, logger):
    begin = datetime.now()
    file_save = filename.replace('url', 'details')
    file_save = file_save.replace('txt', 'csv')
    with open(filename, 'r') as f:
        arr_link =f.readlines()
        arr_link = [x.replace('\n', '') for x in arr_link]

    df = pd.DataFrame()
    keys = ['Company', 'Rating', 'Total Reviews', 'Address', 'Website', 'Phone', 'Image Url']
    for idx, link in enumerate(arr_link):
        print()
        details_dict = dict.fromkeys(keys, None)
        print('link:', link)
        logger.info(f'link: {link}')
        driver.get(link)
        time.sleep(random.randint(3,7))
        try:
            name =driver.find_element_by_class_name('DUwDvf.fontHeadlineLarge').text
        except: name = None
        try:
            star = driver.find_element_by_class_name('F7nice.mmu3tf').text
        except: star = None
        try:
            num_reviews = driver.find_element_by_class_name('mgr77e').text
        except: num_reviews = None
        try:
            img = driver.find_element_by_class_name('RZ66Rb.FgCUCc img').get_attribute('src')
        except: img = None
        print(idx, name)
        details_dict['Company'] = name
        details_dict['Rating'] = star
        details_dict['Total Reviews'] = num_reviews
        details_dict['Image Url'] = img

        try:
            details_element = driver.find_elements_by_class_name('RcCsl.fVHpi.w4vB1d.NOE9ve.M0S7ae.AG25L')
            for x in details_element:
                detail = x.find_element_by_class_name('CsEnBe').get_attribute('aria-label')
                detail_split = detail.split(':')
                if len(detail_split) == 1:
                    continue
                key = detail_split[0]
                value = detail_split[1]
                details_dict[key] = value
        except:
            pass

        # crawl list image
        res_arr_img_url = []
        try:
            driver.find_element_by_class_name('RZ66Rb.FgCUCc img').click()
            time.sleep(5)
            try:
                script = "function sleep(ms){return new Promise(resolve=>setTimeout(resolve,ms))};var el_list=document.getElementsByClassName('U39Pmb');var count=1;while(count<10){count+=1;el_list=document.getElementsByClassName('U39Pmb');el=el_list[el_list.length-1];el.scrollTop=el.scrollHeight;el.scrollIntoView();await sleep(300);console.log('count:',count)}"
                driver.execute_script(script)
                arr_img_url = driver.find_elements_by_class_name('U39Pmb')
                print('len(arr_img_url)', len(arr_img_url))
                logger.info(f'Total img have: {len(arr_img_url)}')
                for img_url in arr_img_url:
                    try:
                        raw_ele = img_url.get_attribute('style')
                        image_url = raw_ele.split('\"')[1]
                        if 'http' not in image_url:
                            # print('abc')
                            pass
                        else:
                            res_arr_img_url.append(image_url)
                    except:
                        pass
            except:
                pass
        except:
            pass
        print('res_arr_img_url: ', len(res_arr_img_url))
        logger.info(f'Total img crawl: {len(res_arr_img_url)}')
        details_dict['List image'] = res_arr_img_url

        print('details_dict', details_dict)
        logger.info(f'details_dict: {json.dumps(details_dict)}')
        time.sleep(5)

        df = df.append(details_dict, ignore_index=True)
        if idx> 0 and idx %5==0:
            df.to_csv(file_save, index=False)

    # save
    print(datetime.now())
    end = datetime.now()
    print('Time run:', (end-begin)/60, 'minutes')
    print('Total extract:', len(df))

    logger.info(f'Time run: {(end - begin) / 60} minutes')
    logger.info(f'Total extract: {len(df)}')


    df.to_csv(file_save, index=False)
    return

def crawl_details(logger=logger_details):
    arr_filename_url = glob.glob('data/url/*.txt')
    arr_filename_details = glob.glob('data/details/*.csv')

    #     arr_town_crawl = [x.split("\\")[1].split('.')[0] for x in arr_filename_details]
    arr_town_crawl = [x.split("details/")[1].split('.')[0] for x in arr_filename_details]

    with open('data/crawled_town_details.txt', 'r') as f:
        arr_crawled_town_details = f.readlines()
        arr_crawled_town_details = [x.replace('\n', '') for x in arr_crawled_town_details]
        f.close()

    driver = None
    for idx, filename in enumerate(arr_filename_url):
        logger.info('#------------------------------------')
        print('filename:', filename)
        if driver is None:
            print('init driver')
            driver = initDriver()
        
        if idx>0 and idx % 5==0:
            driver.quit()
            for _ in tqdm(range(MINUTE_WAIT),desc=f"Delay {MINUTE_WAIT} minutes..."):
                time.sleep(60)
            driver = initDriver()
            
        town = filename.split('url/')[1].split('.')[0]
        if town not in arr_town_crawl and town not in arr_crawled_town_details:
            print(f'Crawling {town}')
            logger.info(f'Crawling {remove_accents(town)}')
            time.sleep(3)
            try:
                crawl_restaurant_details(filename,driver, logger=logger_details)
                with open('data/crawled_town_details.txt', 'a') as f:
                    f.write(town+'\n')
                    f.close()
            except Exception as e:
                print(e)
                driver.quit()
        else:
            print(f'{town} is crawled')
            continue
    return


import argparse
def run(args):
    name = args.name
    if name == 'crawl_url':
        crawl_url()
    elif name == 'crawl_details':
        crawl_details()
    else:
        print(f'Not have function {name}')

    return

parser = argparse.ArgumentParser(description='Say hello')
parser.add_argument('--name', help='function run: crawl_url/crawl_details')
args = parser.parse_args()
if __name__ =='__main__':
    run(args)
