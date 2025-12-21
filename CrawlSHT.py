# -*- coding: utf-8 -*-
"""CLI utility for crawling forum pages and persisting magnet links."""

from __future__ import annotations

import argparse
import datetime
import os
import time
from pathlib import Path
from typing import Iterable

import requests

from crawler_core import CrawlerConfig, ForumCrawler, sanitize_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量爬取论坛磁力链接")
    parser.add_argument("--base-url", default="https://btd5.thsf7.net", help="论坛根地址")
    parser.add_argument("--forum-id", default="2", help="论坛板块ID，如103")
    parser.add_argument("--start-page", type=int, default=1, help="起始页码（包含）")
    parser.add_argument("--end-page", type=int, default=5, help="结束页码（包含）")
    parser.add_argument("--cookie", default=os.environ.get("CRAWLER_COOKIE"), help="访问论坛时使用的Cookie")
    parser.add_argument(
        "--image-cookie",
        default=os.environ.get("CRAWLER_IMAGE_COOKIE"),
        help="下载图片时使用的Cookie",
    )
    parser.add_argument("--output", help="磁力链接输出文件路径")
    parser.add_argument(
        "--save-images",
        action="store_true",
        help="是否下载帖子中的图片",
    )
    parser.add_argument(
        "--figures-dir",
        default="data/figures",
        help="保存图片的根目录（仅在 --save-images 开启时使用）",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="每个页面之间的延迟，单位秒",
    )
    return parser


def resolve_output_path(output: str | None) -> Path:
    if output:
        path = Path(output)
    else:
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        path = Path("data") / f"magnet_file_{timestamp}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def crawl_forum(args: argparse.Namespace) -> None:
    config = CrawlerConfig(
        base_url=args.base_url.rstrip("/"),
        cookie=args.cookie,
        image_cookie=args.image_cookie,
    )
    crawler = ForumCrawler(config)
    output_path = resolve_output_path(args.output)
    image_root = None
    if args.save_images:
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        image_root = Path(args.figures_dir) / f"forum_{args.forum_id}_{timestamp}"
        image_root.mkdir(parents=True, exist_ok=True)

    total_magnets = 0
    total_images = 0

    with output_path.open("w", encoding="utf-8") as handle:
        for page in range(args.start_page, args.end_page + 1):
            forum_url = f"{config.base_url}/forum-{args.forum_id}-{page}.html"
            print(f"\n=== 正在处理第 {page} 页: {forum_url}")
            try:
                thread_paths = crawler.fetch_thread_paths_from_forum_url(forum_url)
            except requests.RequestException as exc:
                print(f"无法获取第 {page} 页的帖子: {exc}")
                continue

            if not thread_paths:
                print("未发现帖子链接，跳过。")
                continue

            for thread_path in thread_paths:
                thread_url = f"{config.base_url.rstrip('/')}/{thread_path}"
                print(f"  -> 解析帖子: {thread_url}")
                try:
                    magnets, image_urls, soup = crawler.fetch_thread_details(thread_path)
                except requests.RequestException as exc:
                    print(f"     无法访问帖子: {exc}")
                    continue

                if magnets:
                    for magnet in magnets:
                        handle.write(magnet + "\n")
                    total_magnets += len(magnets)
                    print(f"     已写入 {len(magnets)} 条磁力链接")
                else:
                    print("     未发现磁力链接")

                if args.save_images and image_urls and image_root is not None:
                    thread_name = sanitize_name(soup.title.text if soup.title else thread_path)
                    destination = image_root / thread_name
                    saved, skipped = crawler.download_images(image_urls, str(destination))
                    total_images += saved
                    print(f"     图片保存结果: {saved} 成功, {len(skipped)} 跳过")

            time.sleep(args.delay)

    print("\n===== 爬取完成 =====")
    print(f"磁力链接总数: {total_magnets}")
    if args.save_images:
        print(f"成功保存图片: {total_images}")
        print(f"图片根目录: {image_root}")
    print(f"输出文件: {output_path}")


def main() -> None:
    args = build_parser().parse_args()
    crawl_forum(args)


if __name__ == "__main__":
    main()
