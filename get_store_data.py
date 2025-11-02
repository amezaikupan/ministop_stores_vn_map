import marimo

__generated_with = "0.17.2"
app = marimo.App(width="medium")


@app.cell
def _():
    data = data[data['Availability'] == 'Mở cửa 24 giờ']
    data.loc[len(data)] = [
        'T5-B01.03+04, tại tầng 1 thuộc dự án Khu nhà ở chung cư cao cấp Masteri Thảo Điền, số 159 Võ Nguyên Giáp, Phường Thảo Điền, Thành phố Hồ Chí Minh', 'Số điện thoại: (028) 3620 2963', 'Mở cửa 24 giờ'
    ]
    return (data,)


@app.cell
def _():
    return


@app.cell
def _(stores_err_info):
    stores_err_locations = [str(info).split("<br/>") for info in stores_err_info[:12]]
    stores_err_locations

    stores_err_info
    return


@app.cell
def _(stores_info):
    stores_info
    return


@app.cell
def _(BeautifulSoup, re):
    import pandas as pd 
    import time 
    from diskcache import Cache

    pages = range(15)
    cache = Cache("stores_cache")

    stores_info = []
    stores_err_info = []
    for page in pages:
        base_url = f'https://www.ministop.vn/vi/ms?page={page}'
        _res = re.get(base_url)

        try:
            _res = re.get(base_url, timeout=10)
            _res.raise_for_status()
        except re.RequestException as e:
            print(f"Failed to fetch page {page}: {e}")
            continue

        _soup = BeautifulSoup(_res.text, "html.parser")
        for store in _soup.select("#block-fluffiness-content p"):
            spans = store.select('span')
            if store in cache:
                continue 

            if len(spans) == 3:
                store_info = {
                    "Location": spans[0].get_text(strip=True),
                    "Phone": spans[1].get_text(strip=True),
                    "Availability": spans[2].get_text(strip=True)
                }
            elif len(spans) == 4: 
                store_info = {
                    "Location": spans[0].get_text(strip=True) + " " + spans[1].get_text(strip=True),
                    "Phone": spans[2].get_text(strip=True),
                    "Availability": spans[3].get_text(strip=True)
                }
            else:
                print("len of span is ", len(spans))
                print(store, spans)
            
            stores_info.append(store_info)
            cache[store] = store_info

            # print("Store info", stores_info)
            # break
        
            # stores_info.append(store_info)
        time.sleep(1)
    return stores_err_info, stores_info


@app.cell
def _(soup):
    soup.select(".pager__item--number")
    return


@app.cell
def _(soup):
    soup.select("#block-fluffiness-content p")[0].select('span')
    return


@app.cell
def _(BeautifulSoup, response):
    soup = BeautifulSoup(response.text, 'html.parser')
    return (soup,)


@app.cell
def _(re, url):
    response = re.get(url)
    return (response,)


@app.cell
def _():
    url = 'https://www.ministop.vn/vi/ms'
    return (url,)


@app.cell
def _():
    import requests as re 
    from bs4 import BeautifulSoup
    return BeautifulSoup, re


if __name__ == "__main__":
    app.run()
