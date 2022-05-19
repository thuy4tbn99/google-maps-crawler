# google-maps-crawler
- Crawl data from [Google-map](https://www.google.com/maps) by python-Selenium
- The project was initially made to collect restaurant locations in Hanoi, Vietnam
- Default use query_search: "crawl restaurant near {town}"
  + {town} is in Hanoi, Vietnam (This is listed in [data/DS_tinh_thanh.csv](https://github.com/thuy4tbn99/google-maps-crawler/blob/master/data/DS_tinh_thanh.csv))

## Installation
conda env create -f crawler.yml --prefix [environment-path]

## Run
- Crawl all restaurant url and save in csv file at data/url:
  * python crawl_restaurant.py --name crawl_url

- After run crawl_url, crawl restaurant info (contains: Name, Rating, Total Reviews, Address, Website, Phone, List Image) and save in csv file at data/details:
  * python crawl_restaurant.py --name crawl_details

- Crawl image from data/details/*.csv and save in folder data/images/: 
  * python crawl_image.py

## Customize
- If you want to crawl another place instead of restaurant, you can modify _query_search_ in function [_crawl_url_] in [crawl_restaurant.py](https://github.com/thuy4tbn99/google-maps-crawler/blob/master/crawl_restaurant.py)


