import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import requests 
    from bs4 import BeautifulSoup


    url = 'https://www.circlek.com.vn/vi/he-thong-circle-k/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return BeautifulSoup, soup


@app.cell
def _(soup):
    circle_k_stores_list = []

    for store in soup.select(".item"): 
        print(store)
        tags = store.select("a")
        for tag in tags:
            if tag.has_attr("data-lat"):
                lat = tag.get("data-lat")
                lng = tag.get("data-lng")
 
        addr = store.select("p")
        clean_addr = addr[0].get_text(separator=', ')

        store_info = {
            'address': clean_addr, 
            'latitude': lat,
            'longitude': lng
        }

        circle_k_stores_list.append(store_info)
    return (circle_k_stores_list,)


@app.cell
def _(circle_k_stores_list):
    import pandas as pd 

    data = pd.DataFrame(circle_k_stores_list)
    data.to_csv('data/2 processed/circle_k_stores_location_geocoded.csv', index=False)
    return


@app.cell
def _(BeautifulSoup):
    dummy_string = '''
    <div class="item">
    <p style="">40 Trung Hòa<br/>Phường Trung Hòa<br/>Quận Cầu Giấy<br/>Hà Nội</p>
    <p>Phone: <a href="tel:+84-24-3204-5464" style="display: inline">+84 24 3204 5464</a></p>
    <a class="click_location" data-index="240" data-lat="21.0146675" data-lng="105.8016853" href="javascript:;"><i class="fa fa-angle-right"></i>Xem vị trí</a>
    <div class="list-ser clearfix"><span class="list-ser-24h"><img alt="" src="https://www.circlek.com.vn/wp-content/uploads/2018/03/bill-pyment-100x54.png" title="Thanh Toán Hóa Đơn"/></span><span class="list-ser-24h"><img alt="" src="https://www.circlek.com.vn/wp-content/uploads/2018/10/credit-card100x54.png" title="Thanh Toán Bằng Thẻ"/></span><span class="list-ser-24h"><img alt="" src="https://www.circlek.com.vn/wp-content/uploads/2016/01/phonecard-100x54.png" title="Thẻ Điện Thoại"/></span><span class="list-ser-24h"><img alt="" src="https://www.circlek.com.vn/wp-content/uploads/2016/01/gamecard-100x54.png" title="Thẻ Game"/></span><span class="list-ser-24h"><img alt="" src="https://www.circlek.com.vn/wp-content/uploads/2016/01/1.png" title="Thức Ăn &amp; Thức Uống"/></span></div>
    </div>
    '''
    _soup = BeautifulSoup(dummy_string, 'html.parser')
    _soup.select('.item')[0].select('a')
    return


if __name__ == "__main__":
    app.run()
