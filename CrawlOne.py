# -*- coding: utf-8 -*-
"""Crawl a single thread for magnet links and optional images."""

from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path

import requests

from crawler_core import CrawlerConfig, ForumCrawler, sanitize_name

def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='爬取指定网址的磁力链接和图片')
    parser.add_argument('url', help='要爬取的网址')
    parser.add_argument('--base-url', default=None, help='可选：覆盖默认站点根地址')
    parser.add_argument('--cookie', default=os.environ.get("CRAWLER_COOKIE"), help='访问帖子使用的Cookie')
    parser.add_argument('--image-cookie', default=os.environ.get("CRAWLER_IMAGE_COOKIE"), help='下载图片使用的Cookie')
    parser.add_argument('--save-images', action='store_true', help='是否保存图片')
    parser.add_argument('--output-file', default=None, help='磁力链接输出文件路径')
    parser.add_argument('--image-dir', default=None, help='图片保存目录')
    return parser.parse_args()


def parse_content(crawler: ForumCrawler, url: str, *, save_images=False, image_dir=None):
    """
    通过共享crawler抓取磁力链接并可选保存图片。
    """
    print(f"\n正在爬取网址: {url}")
    try:
        magnets, image_urls, soup = crawler.fetch_thread_details(url)
    except requests.RequestException as exc:
        print(f"ERROR: 无法访问网页: {exc}")
        return []

    if magnets:
        print(f"\n===== 提取磁力链接（{len(magnets)} 条）=====")
        for i, magnet in enumerate(magnets, 1):
            print(f"[{i}] {magnet}")
    else:
        print("\n未找到磁力链接")

    if save_images and image_urls:
        print(f"\n===== 提取图片（{len(image_urls)} 张）=====")
        for i, image in enumerate(image_urls, 1):
            print(f"[{i}] {image}")

        if image_dir is None:
            now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            title = soup.title.text if soup.title else "thread"
            image_dir = Path("data/figures") / f"{sanitize_name(title)}_{now}"
        else:
            image_dir = Path(image_dir)

        image_dir.mkdir(parents=True, exist_ok=True)
        saved, skipped = crawler.download_images(image_urls, str(image_dir))
        print(f"图片保存完成: 成功 {saved}，跳过 {len(skipped)}，路径 {image_dir}")
        if skipped:
            for item in skipped[:3]:
                print(f"  - 跳过: {item}")
    elif save_images:
        print("\n未找到可下载的图片")

    return magnets


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

    base_url = args.base_url or os.environ.get("CRAWLER_BASE_URL")
    config = CrawlerConfig(
        base_url=base_url or "https://tepm.kpqq4.net",
        cookie=args.cookie,
        image_cookie=args.image_cookie,
    )
    crawler = ForumCrawler(config)

    # 爬取内容
    magnet_links = parse_content(
        crawler,
        url=args.url,
        save_images=args.save_images,
        image_dir=args.image_dir,
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
