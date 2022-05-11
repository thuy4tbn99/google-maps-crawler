import random
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import os
from time import sleep
from datetime import datetime


def initDriver():
    CHROMEDRIVER_PATH = 'C:\\Program Files (x86)\\chromedriver.exe'
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
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                              options=chrome_options
                              )
    return driver


def read_ds():
    df = pd.read_csv('./data/DS_tinh_thanh.csv')
    df_hn = df[df['Tỉnh Thành Phố']=='Thành phố Hà Nội']
    list_district = ['Quận Ba Đình', 'Quận Hoàn Kiếm', 'Quận Tây Hồ', 'Quận Cầu Giấy','Quận Đống Đa',
                          'Quận Hai Bà Trưng','Quận Hoàng Mai', 'Quận Thanh Xuân','Quận Nam Từ Liêm',
                          'Quận Bắc Từ Liêm', 'Quận Hà Đông']
    df_hn_core = df_hn[df_hn['Quận Huyện'].isin(list_district)]
    arr_town = df_hn_core['Phường Xã'].tolist()

    driver = initDriver()
    for town in arr_town[:2]:
        query_search = f'restaurant near {town}'
        print('query_search:', query_search)
        crawl_restaurant(driver, query_search, town)

    return

def crawl_restaurant(driver, query_search, town):
    begin = datetime.now()
    driver.get('https://maps.google.com/')
    time.sleep(3)
    inputSearchEle = driver.find_element_by_class_name('tactile-searchbox-input')
    inputSearchEle.send_keys(query_search)
    inputSearchEle.send_keys(Keys.ENTER)
    time.sleep(8)
    script_js = "function sleep(ms){return new Promise(resolve=>setTimeout(resolve,ms))};var el_list=document.getElementsByClassName('hfpxzc');var count=1;while(el_list.length<20||count>100){count+=1;el_list=document.getElementsByClassName('hfpxzc');el=el_list[el_list.length-1];el.scrollTop=el.scrollHeight;el.scrollIntoView();await sleep(1000);console.log(el_list.length);if(el_list.length==20){count=1};console.log('count:',count)}"
    driver.execute_script(script_js)

    arr_res_ele = driver.find_elements_by_class_name('hfpxzc')
    arr_link_res = [x.get_attribute('href') for x in arr_res_ele]

    all_link_res = []
    all_link_res.extend(arr_link_res)

    # next-page
    while(True):
        try:
            driver.find_element_by_id('ppdPk-Ej1Yeb-LgbsSe-tJiF1e').click()
            time.sleep(5)
            driver.execute_script(script_js)
            arr_link_res = [x.get_attribute('href') for x in driver.find_elements_by_class_name('hfpxzc')]
            print(len(arr_link_res))
            all_link_res.extend(arr_link_res)
        except Exception as e:
            print(e)
            break

    print(len(all_link_res), all_link_res[10])
    time.sleep(5)
    with open(f'data/url/restaurant_{town}.txt', 'w') as f:
        for link in all_link_res:
            f.write("%s\n" % link)
        f.close()

    end = datetime.now()
    print(f'Time run {town}: ', (end-begin)/60, 'minutes')
    print()
    # driver.quit()
    # driver.close()

    return


def crawl_restaurant_details(filename):
    begin = datetime.now()
    file_save = filename.replace('url', 'details')
    file_save = file_save.replace('txt', 'csv')
    with open(filename, 'r') as f:
        arr_link =f.readlines()
        arr_link = [x.replace('\n', '') for x in arr_link]
    driver = initDriver()
    df = pd.DataFrame()
    keys = ['Company', 'Rating', 'Total Reviews', 'Address', 'Website', 'Phone', 'Image Url']
    for idx, link in enumerate(arr_link):
        print()
        details_dict = dict.fromkeys(keys, None)
        print('link:', link)
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
        details_dict['List image'] = res_arr_img_url


        print('details_dict', details_dict)
        df = df.append(details_dict, ignore_index=True)
        if idx >3 and 0: # luôn sai
        # if idx > 3:
            break
        if idx> 0 and idx %5==0:
            df.to_csv(file_save, index=False)
            break

    # save
    print(datetime.now())
    end = datetime.now()
    print('Time run:', (end-begin)/60, 'minutes')
    print('Total extract:', len(df))


    df.to_csv(file_save, index=False)
    return

if __name__ =='__main__':
    # crawl_restaurant()
    # read_ds()

    crawl_restaurant_details(filename='./data/url/restaurant_Phường Phúc Xá.txt')