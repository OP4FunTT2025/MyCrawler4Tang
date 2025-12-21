#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级单元测试：验证解析逻辑无需访问真实站点。
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from crawler_core import extract_magnet_links, extract_thread_paths, sanitize_name

FORUM_HTML = """
<html>
  <body>
    <a href="thread-100-2-2.html">Thread A</a>
    <a href="/thread-101-1-1.html">Thread B</a>
    <a href="https://example.com/thread-102-5-1.html">Thread C</a>
    <a href="misc-ignored.html">Ignore</a>
  </body>
</html>
"""

THREAD_HTML = """
<html>
  <head><title>磁力合集 精选</title></head>
  <body>
    <ul>
      <li>magnet:?xt=urn:btih:AAA111</li>
      <li>magnet:?xt=urn:btih:BBB222</li>
      <li>http://example.com/not-magnet</li>
    </ul>
    <img src="/images/pic1.jpg">
    <img file="https://cdn.example.com/pic2.png">
  </body>
</html>
"""


def test_extract_thread_paths():
    links = extract_thread_paths(FORUM_HTML)
    assert links == [
        "thread-100-1-2.html",
        "thread-101-1-1.html",
        "thread-102-1-1.html",
    ]
    print("✓ extract_thread_paths 输出符合预期")


def test_extract_magnet_links():
    soup = BeautifulSoup(THREAD_HTML, "lxml")
    magnets = extract_magnet_links(soup)
    assert magnets == ["magnet:?xt=urn:btih:AAA111", "magnet:?xt=urn:btih:BBB222"]
    print("✓ extract_magnet_links 捕获了两个磁力链接")


def test_sanitize_name():
    assert sanitize_name(" 图片 / Test ") == "图片___Test"
    assert sanitize_name("   ") == "unnamed"
    print("✓ sanitize_name 能处理空白和非法字符")


if __name__ == "__main__":
    print("开始执行解析逻辑单元测试...")
    test_extract_thread_paths()
    test_extract_magnet_links()
    test_sanitize_name()
    print("全部测试通过 ✅")
