#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫功能测试脚本
用于测试parse_topzh_use_bs和parse_content_use_bs函数是否能够正常访问网页并提取数据
"""

import requests
from bs4 import BeautifulSoup
import time

# 使用与app.py中相同的headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    "Cookie": "cPNj_2132_saltkey=KhbhYZHU; cPNj_2132_lastvisit=1764373583; cPNj_2132_atarget=1; cPNj_2132_lastfp=4a8b2ed4d942c6bc0f64e1021691ecc7; sl-session=i7J8TKI4MGnxQkMSruQiWQ==; _safe=LFzQp0o00mj8Z2I0; cPNj_2132_viewid=tid_3164292; cPNj_2132_lastact=1764681618%09forum.php%09forumdisplay; cPNj_2132_st_t=0%7C1764681618%7Cd50ef50766f62b42e905a599b4b9a60e; cPNj_2132_forum_lastvisit=D_95_1764416438D_151_1764419725D_37_1764419885D_141_1764420846D_103_1764681618; cPNj_2132_visitedfid=103D141D37D151D95"
}

def test_parse_topzh_use_bs():
    """测试parse_topzh_use_bs函数"""
    print("=" * 50)
    print("测试 parse_topzh_use_bs 函数")
    print("=" * 50)
    
    # 测试URL（论坛板块页面）
    test_url = "https://btd5.thsf7.net/forum-103-1.html"
    
    try:
        start_time = time.time()
        response = requests.get(url=test_url, headers=headers, timeout=10)
        response_time = time.time() - start_time
        
        print(f"✓ 成功访问网页: {test_url}")
        print(f"  响应状态码: {response.status_code}")
        print(f"  响应时间: {response_time:.2f} 秒")
        print(f"  页面大小: {len(response.content)} 字节")
        
        # 解析网页
        soup = BeautifulSoup(response.content, "lxml")
        links = soup.find_all('a')
        print(f"  页面中找到 {len(links)} 个链接")
        
        # 提取有效链接
        valid_links = set()
        for link in links:
            link_url = link.get('href')
            if link_url:
                if link_url.startswith('thread') and link_url.endswith('.html'):
                    valid_links.add(link_url)
        
        print(f"  提取到 {len(valid_links)} 个有效帖子链接")
        
        if valid_links:
            print("  部分有效链接示例:")
            for i, link in enumerate(list(valid_links)[:5]):  # 只显示前5个
                print(f"    {i+1}. {link}")
        
        return valid_links
        
    except Exception as e:
        print(f"✗ 访问网页失败: {str(e)}")
        return set()

def test_parse_content_use_bs(post_links):
    """测试parse_content_use_bs函数"""
    if not post_links:
        print("没有可用的帖子链接进行测试")
        return
    
    print("\n" + "=" * 50)
    print("测试 parse_content_use_bs 函数")
    print("=" * 50)
    
    # 只测试前3个帖子
    test_links = list(post_links)[:3]
    
    for i, link in enumerate(test_links, 1):
        post_url = f"https://btd5.thsf7.net/{link}"
        print(f"\n测试帖子 {i}/{len(test_links)}: {post_url}")
        
        try:
            start_time = time.time()
            r = requests.get(url=post_url, headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            print(f"✓ 成功访问帖子页面")
            print(f"  响应状态码: {r.status_code}")
            print(f"  响应时间: {response_time:.2f} 秒")
            
            # 解析网页
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.content, "lxml")
            
            # 提取磁力链接
            magnet_links = []
            for li in soup.find_all('li'):
                magnet_link = li.get_text()
                if magnet_link.startswith('magnet:?xt'):
                    magnet_links.append(magnet_link)
            
            print(f"  提取到 {len(magnet_links)} 个磁力链接")
            
            if magnet_links:
                print("  部分磁力链接示例:")
                for j, magnet in enumerate(magnet_links[:2]):  # 只显示前2个
                    print(f"    {j+1}. {magnet[:60]}...")  # 只显示前60个字符
            
        except Exception as e:
            print(f"✗ 访问帖子失败: {str(e)}")

def test_website_accessibility():
    """测试网站整体可访问性"""
    print("\n" + "=" * 50)
    print("测试网站整体可访问性")
    print("=" * 50)
    
    test_urls = [
        "https://btd5.thsf7.net/",
        "https://btd5.thsf7.net/forum-103-1.html",
        "https://btd5.thsf7.net/forum-103-2.html"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url=url, headers=headers, timeout=10)
            print(f"✓ {url} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"✗ {url} - 无法访问: {str(e)}")

if __name__ == "__main__":
    print("开始测试爬虫功能...")
    print("测试时间: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # 测试网站可访问性
    test_website_accessibility()
    
    # 测试帖子链接提取
    post_links = test_parse_topzh_use_bs()
    
    # 测试磁力链接提取
    test_parse_content_use_bs(post_links)
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
