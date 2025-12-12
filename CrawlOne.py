# -*- coding: utf-8 -*-
# @Author  : OnePerson
# @Time    : 2025/12/1
# @Desc    : 爬取指定网址的磁力链接和图片

import requests
from bs4 import BeautifulSoup
import os
import datetime
import argparse
import sys

def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='爬取指定网址的磁力链接和图片')
    parser.add_argument('url', help='要爬取的网址')
    parser.add_argument('--save-images', action='store_true', help='是否保存图片')
    parser.add_argument('--output-file', default=None, help='磁力链接输出文件路径')
    parser.add_argument('--image-dir', default=None, help='图片保存目录')
    return parser.parse_args()


def parse_content(url, save_images=False, image_dir=None):
    """
    爬取指定网址的磁力链接和图片
    
    Args:
        url: 要爬取的网址
        save_images: 是否保存图片
        image_dir: 图片保存目录
        
    Returns:
        list: 磁力链接列表
    """
    # 定义请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        "Cookie": "cPNj_2132_saltkey=IJz8uk80; cPNj_2132_lastvisit=1764366895; cPNj_2132_lastfp=0fdb7fc9f2ebcac91b1e52ed50162555; cPNj_2132_atarget=1; cPNj_2132_st_p=0%7C1765372755%7C2eab28c111965c6916036201fe3b0d8c; sl-session=bhxbFg4lPGm5/a8Ca82/QA==; cPNj_2132_st_t=0%7C1765463539%7C24b1cb5a8f98e7c175beadf2ecdde0b2; cPNj_2132_forum_lastvisit=D_37_1765378591D_2_1765378778D_151_1765378948D_141_1765379102D_103_1765463539; cPNj_2132_visitedfid=103D141D151D2D37D38; _safe=xkZ9iIiIi9u7jcAC; cPNj_2132_lastact=1765465693%09forum.php%09viewthread; cPNj_2132_viewid=tid_3182886"
    }
    
    image_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        "Cookie": "cf_clearance=g_P5Eml.uqRnBRosJ1YO4QcXDXUYs_hMFFlO2QlIbxA-1765463791-1.2.1.1-d0zzfiajVwC_Ey6xtppIUuKaVvPF3wutJu3vMkzc3BfjOmh4.XN57zK0ZNRTYpF9HwErtL_cso1bUb4V8AqQ35ckz6iE1dFMaZDlNR8UE0xI41VBZqdy2p3Km2bH4F7myXpg62Vzzez8B8vIxCsQMd22e3bNAbVAlM1UmJaWCepVrP.ODHK5UVR8Vcc7CamnwsUQjDm7PP1omZR6P9Z1A16iyGXBgLrvH3NXj_MrVHs"
    }
    
    print(f"\n正在爬取网址: {url}")
    
    try:
        # 发送请求获取网页内容
        r = requests.get(url=url, headers=headers, timeout=10)
        r.encoding = 'utf-8'
        print(f"网页状态码: {r.status_code}")
        
        if r.status_code != 200:
            print(f"ERROR: 无法访问网页，状态码: {r.status_code}")
            return []
        
        # 解析网页内容
        soup = BeautifulSoup(r.content, "lxml")
        
        # 1. 提取磁力链接
        print("\n===== 提取磁力链接 =====")
        magnet_links = []
        for link in soup.find_all('li'):
            magnet_link = link.get_text()
            if magnet_link.startswith('magnet:?xt'):
                magnet_links.append(magnet_link)
        
        if magnet_links:
            print(f"找到 {len(magnet_links)} 个磁力链接:")
            for i, magnet_link in enumerate(magnet_links, 1):
                print(f"[{i}] {magnet_link}")
        else:
            print("未找到磁力链接")
        
        # 2. 提取图片URL
        print("\n===== 提取图片 =====")
        image_urls = []
        for img in soup.find_all('img'):
            # 尝试不同的属性名
            image_url = img.get('file') or img.get('src')
            if image_url:
                # 如果是相对URL，转换为绝对URL
                if not image_url.startswith(('http://', 'https://')):
                    if image_url.startswith('/'):
                        # 从原始URL中提取基础URL
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        image_url = f"{base_url}{image_url}"
                    else:
                        continue  # 跳过无法处理的相对路径
                image_urls.append(image_url)
        
        if image_urls:
            print(f"找到 {len(image_urls)} 张图片:")
            for i, image_url in enumerate(image_urls, 1):
                print(f"[{i}] {image_url}")
        else:
            print("未找到图片")
        
        # 3. 保存图片
        if save_images and image_urls:
            print("\n===== 保存图片 =====")
            
            # 确定图片保存目录
            if image_dir is None:
                # 使用当前时间创建目录名
                now = datetime.datetime.now()
                formatted_datetime = now.strftime("%Y_%m_%d_%H_%M_%S")
                # 尝试从页面标题获取信息
                page_title = soup.title.text if soup.title else "unknown_page"
                # 清理标题中的非法字符
                import re
                page_title = re.sub(r'[\\/*?"<>|]', "_", page_title)
                # 限制标题长度
                if len(page_title) > 50:
                    page_title = page_title[:50]
                image_dir = f"data/figures/{page_title}_{formatted_datetime}"
            
            # 创建保存目录
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
                print(f"创建图片保存目录: {image_dir}")
            
            # 保存图片
            saved_count = 0
            for i, image_url in enumerate(image_urls, 1):
                try:
                    print(f"\n保存图片 {i}/{len(image_urls)}: {image_url}")
                    
                    # 检测图片是否可访问
                    head_response = requests.head(image_url, headers=image_headers, timeout=5, allow_redirects=True)
                    if head_response.status_code != 200:
                        print(f"  ❌ 图片不可访问 (状态码: {head_response.status_code})")
                        continue
                    
                    content_type = head_response.headers.get('Content-Type', '')
                    if not content_type.startswith('image/'):
                        print(f"  ❌ 不是有效图片类型 ({content_type})")
                        continue
                    
                    # 下载图片
                    response = requests.get(image_url, headers=image_headers, timeout=10)
                    if response.status_code != 200:
                        print(f"  ❌ 下载失败，状态码: {response.status_code}")
                        continue
                    
                    # 确定文件名
                    filename = image_url.split('/')[-1]
                    if not filename:
                        filename = f"image_{i}.jpg"
                    
                    # 确保文件名合法
                    filename = filename.split('?')[0]  # 移除URL参数
                    if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                        filename += '.jpg'  # 默认使用jpg扩展名
                    
                    # 保存图片
                    save_path = os.path.join(image_dir, filename)
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"  ✅ 保存成功: {save_path}")
                    saved_count += 1
                    
                except Exception as e:
                    print(f"  ❌ 处理失败: {str(e)}")
                    continue
            
            print(f"\n图片保存完成: 成功保存 {saved_count}/{len(image_urls)} 张图片到 {image_dir}")
        
        return magnet_links
        
    except Exception as e:
        print(f"ERROR: 爬取过程中发生错误: {str(e)}")
        return []


def save_magnet_links(magnet_links, output_file=None):
    """
    保存磁力链接到文件
    """
    if not magnet_links:
        return
    
    if output_file is None:
        # 使用当前时间创建文件名
        now = datetime.datetime.now()
        formatted_datetime = now.strftime("%Y_%m_%d_%H_%M_%S")
        output_file = f"data/magnet_file_{formatted_datetime}.txt"
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for magnet_link in magnet_links:
                f.write(magnet_link + '\n')
        print(f"\n磁力链接已保存到: {output_file}")
    except Exception as e:
        print(f"ERROR: 保存磁力链接失败: {str(e)}")


def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_args()
    
    # 确保data目录存在
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # 爬取内容
    magnet_links = parse_content(
        url=args.url,
        save_images=args.save_images,
        image_dir=args.image_dir
    )
    
    # 保存磁力链接
    save_magnet_links(magnet_links, args.output_file)
    
    print(f"\n===== 爬取完成 =====")
    print(f"磁力链接数量: {len(magnet_links)}")
    if args.save_images:
        print("图片保存: 已启用")
    else:
        print("图片保存: 未启用")


if __name__ == '__main__':
    main()