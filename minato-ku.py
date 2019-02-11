# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import pandas as pd
from pandas import Series, DataFrame
import time

# URL(港区、渋谷区、千代田区、品川区)
url = 'https://suumo.jp/jj/chintai/ichiran/FR301FC001/?shkr1=03&shkr3=03&cb=8.0&shkr2=03&ts=1&smk=&mt=9999999&sc=13101&sc=13103&sc=13113&sc=13109&ar=030&bs=040&shkr4=03&ct=10.0&cn=10&tc=0400101&ta=13&mb=0&fw2=&et=9999999'

# Grep Data
result = requests.get(url)
raw_data = result.content

# Get Object Data
soup = BeautifulSoup(raw_data, 'html.parser')

# Get pages number
body = soup.find("body")
pages = body.find_all("div",{'class':'pagination pagination_set-nav'})
pages_text = str(pages)
pages_split = pages_text.split('</a></li>\n</ol>')
pages_number = int(pages_split[0].split('>')[-1])

# Create urls for each page
urls = []
urls.append(url)
for i in range(pages_number - 1):
    pg = str(i + 2)
    url_page = url + '&pn=' + pg
    urls.append(url_page)

# Ready objects
data = []
errors = []

# Scrape each page
url_num = 1
for url in urls:
    try:
        result = requests.get(url)
        c = result.content
        soup = BeautifulSoup(c, 'html.parser')

        summary = soup.find("div", {'id': 'js-bukkenList'})
        cassetteitems = summary.find_all("div", {'class': 'cassetteitem'})

        for cas in cassetteitems:
            try:
                # 情報取得用の箱を準備します。
                new = ''            # 新着
                subtitle = ''       # 物件名
                location = ''       # 住所
                station_list = []   # 最寄駅（リスト）
                yrs = ''            # 築年数
                heights = ''        # (建物の）階数
                floor = ''          # （物件のある）階数
                rent = ''           # 家賃
                admin = ''          # 管理費
                others = ''         # その他（敷金／礼金等）
                floor_plan = ''     # 間取り
                area = 0            # 面積

                # 物件名
                subtitle = cas.find("div",{"class":"cassetteitem_content-title"}).string

                # 住所
                location = cas.find("li",{"class":"cassetteitem_detail-col1"}).string

                # 最寄駅
                sta = cas.find("li", {"class":"cassetteitem_detail-col2"})
                stas = sta.find_all("div", {"class":"cassetteitem_detail-text"})
                for s in stas:
                    station_list.append(s.string)

                # 築年数、階数
                col3 = cas.find("li",{"class":"cassetteitem_detail-col3"})
                yrs = col3.find_all('div')[0].string
                heights = col3.find_all('div')[1].string

                tbodies = cas.find_all('tbody')

                for tbody in tbodies:
                    cols = tbody.find_all('td')
                    for i, col in enumerate(cols):
                        if i == 0:
                            try:
                                new = col.span.string.strip('\r\t\n')
                            except:
                                new = ''
                        if i == 2:
                            floor = col.string.strip('\r\t\n')
                        if i == 3:
                            rent = col.find("span", {"cassetteitem_other-emphasis"}).string
                            admin = col.find("span", {"cassetteitem_price--administration"}).string
                        if i == 4:
                            others = col.find("span", {"cassetteitem_price--deposit"}).string
                            others += '/'
                            others += col.find("span", {"cassetteitem_price--gratuity"}).string
                        if i == 5:
                            floor_plan = col.find("span", {"class":"cassetteitem_madori"}).string
                            area = col.find("span", {"cassetteitem_menseki"}).contents[0].string
                
                    data.append([new, subtitle, location, station_list[0], station_list[1], station_list[2], yrs, heights, floor,
                            rent, admin, others, floor_plan, area])
                                    
            except Exception as e:
                errors.append([e, url,len(data)])
                pass

        time.sleep(1) # スクレイピングする際の礼儀として、1秒待ちましょう

    except Exception as e:
        errors.append([e, url, len(data)])
        pass
    
    print("finished ", url_num, "/", pages_number)
    url_num+=1

# data listを DataFrameに変換
df = pd.DataFrame(data, columns=['新着','物件名','住所','立地1','立地2','立地3','築年数','階数','物件階','家賃','管理費','敷金礼金','間取り','面積'])

# csvファイルとして保存
df.to_csv('data/suumo_minato.csv', sep = ',',encoding='utf-8')

# ついでに errors fileも保存
df_errors = pd.DataFrame(errors)
df_errors.to_csv('data/errors_minato.csv', sep = ',', encoding='utf-8')