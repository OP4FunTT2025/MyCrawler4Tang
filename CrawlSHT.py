# -*- coding: utf-8 -*-
# @Author  : OnePerson
# @Time    : 2025/11/29
# @Desc    : https://btd5.thsf7.net/forum-103-1.html

import requests
from bs4 import BeautifulSoup
import os
import urllib
import datetime

# top_zh_url = 'https://btd5.thsf7.net/forum-103-1.html'

# url = 'https://btd5.thsf7.net/thread-3158817-1-1.html'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    "Cookie": "cPNj_2132_saltkey=IJz8uk80; cPNj_2132_lastvisit=1764366895; cPNj_2132_lastfp=0fdb7fc9f2ebcac91b1e52ed50162555; cPNj_2132_atarget=1; cPNj_2132_st_p=0%7C1764464228%7Cb30bb17f02f39447cc68a8a37741985e; cPNj_2132_viewid=tid_3167763; sl-session=BfF5KBJZOmn6RtBgdnhmAw==; _safe=UT6aFTq6pP5LiaQy; cPNj_2132_lastact=1765346214%09forum.php%09forumdisplay; cPNj_2132_st_t=0%7C1765346214%7Cec567d2dfa7cb103cf816b4199a97947; cPNj_2132_forum_lastvisit=D_2_1765346214; cPNj_2132_visitedfid=2D38D37D103"
}

image_headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    "Cookie": "cPNj_2132_saltkey=IJz8uk80; cPNj_2132_lastvisit=1764366895; cPNj_2132_lastfp=0fdb7fc9f2ebcac91b1e52ed50162555; cPNj_2132_atarget=1; cPNj_2132_st_p=0%7C1764464228%7Cb30bb17f02f39447cc68a8a37741985e; cPNj_2132_st_t=0%7C1764679402%7C644a19807b4abb1d91b1699cadadda99; cPNj_2132_visitedfid=38D37D103; cPNj_2132_viewid=tid_3167763; sl-session=BfF5KBJZOmn6RtBgdnhmAw==; _safe=azh5Pzhj15y11j6o; cPNj_2132_lastact=1765345551%09index.php%09"
}

def parse_topzh_use_bs(url_address: str):
    """
    使用beautifulSoup提取网页中的有效链接
    """
    response = requests.get(url=url_address, headers=headers)
    print(response.status_code)
    soup = BeautifulSoup(response.content, "lxml")
    
    results = set()
    
    links = soup.find_all('a')
    for link in links:
        # print(link.get('href'))
        link_url = link.get('href')
        # print(link_url)
        if link_url:
            if link_url.startswith('thread'):
                if link_url.endswith('.html'):
                    # print(link_url)
                    results.add(link_url)
    
    for result in results:
        print(result)        
    
    return results


# print(r.content)

def parse_content_use_bs(url:str):
    """
    使用BeautifulSoup提取网页中的磁力链接
    """
    r = requests.get(url=url, headers=headers)
    r.encoding = 'utf-8'
    print(r.status_code)
    
    soup = BeautifulSoup(r.content, "lxml")
    
    # get magnet link
    magnet_links = []
    for link in soup.find_all('li'):
        magnet_link = link.get_text()
        # print(magnet_link)
        if magnet_link.startswith('magnet:?xt'):
            magnet_links.append(magnet_link)
    for magnet_link in magnet_links:
        print(magnet_link)
    
    # get images
    image_urls = []
    for link in soup.find_all('img'):
        image_url = link.get('file')
        if image_url:
            image_urls.append(image_url)

    for image_url in image_urls:
        print(image_url)
        
    
    # save images
    name = soup.title.text
    name = name.split(' ')
    name = name[0]
    save_dir = "data/"+name
    print(save_dir)
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    for image_url in image_urls:
        filename = image_url.split("/")[-1]
        save_path = os.path.join(save_dir, filename)
        
        re = requests.get(image_url, headers=image_headers)
        print(re.status_code)
        with open(save_path, 'wb') as f:
            for chunk in re.iter_content(chunk_size=128):
                f.write(chunk)
    print(soup.get_text())
    return magnet_links
    
if __name__ == '__main__':
    # 创建data目录（如果不存在）
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # parse_content_use_bs(r.content)
    now = datetime.datetime.now()
    formatted_datetime = now.strftime("%Y_%m_%d_%H_%M")
    print(formatted_datetime)
    file_path = "data/magnet_file"+formatted_datetime+".txt"
    for index in range(1,6):
        top_zh_url_index = "https://btd5.thsf7.net/forum-2-" + str(index) + ".html"
        print(top_zh_url_index)
        urls = parse_topzh_use_bs(top_zh_url_index)
        with open(file_path, 'a') as f:
            for url in urls:
                url = "https://btd5.thsf7.net/" + url
                print(url)
                magnets = parse_content_use_bs(url)
                for magnet in magnets:
                    f.write(magnet+'\n')