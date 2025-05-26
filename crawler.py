#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# === 配置區 ===
SITEMAP_INDEX_URL = 'https://supercell.com/sitemap.xml'
NS                = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
BLOG_PATH_KEYWORD = '/en/games/clashofclans/zh/blog/'
OUTPUT_FILE       = 'coc_blog_with_dates.json'
HEADERS           = {
    'User-Agent': 'Mozilla/5.0 (compatible; MyCrawler/1.0; +https://example.com/bot)'
}
# ==============

def fetch_sitemap_urls():
    resp = requests.get(SITEMAP_INDEX_URL, headers=HEADERS)
    resp.raise_for_status()
    # 如果 requests 沒有正確偵測，強制用 utf-8
    resp.encoding = 'utf-8'
    root = ET.fromstring(resp.text)
    return [sm.find('sm:loc', NS).text for sm in root.findall('sm:sitemap', NS)]

def fetch_blog_urls(sitemap_url):
    resp = requests.get(sitemap_url, headers=HEADERS)
    resp.raise_for_status()
    resp.encoding = 'utf-8'
    root = ET.fromstring(resp.text)
    urls = []
    for url in root.findall('sm:url', NS):
        loc = url.find('sm:loc', NS).text
        if BLOG_PATH_KEYWORD in loc:
            urls.append(loc)
    return urls

def parse_article_date(url):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    # 強制 utf-8
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'lxml')

    # 1) 優先 div[data-test-id="tagline"]
    tag = soup.select_one('div[data-test-id="tagline"]')
    if tag:
        return tag.get_text(strip=True)

    # 2) fallback: time[datetime]
    time_tag = soup.select_one('time[datetime]')
    if time_tag:
        return time_tag.get('datetime', time_tag.get_text(strip=True))

    return ''

def main():
    sitemap_urls = fetch_sitemap_urls()

    all_urls = set()
    for sm_url in sitemap_urls:
        all_urls.update(fetch_blog_urls(sm_url))
    all_urls = sorted(all_urls)
    print(f'共抓到 {len(all_urls)} 篇文章 URL')

    articles = []
    for url in all_urls:
        date = parse_article_date(url)
        print(f'解析：{url} → {date}')
        articles.append({
            'url':  url,
            'date': date
        })

    # 寫檔時使用 utf-8-sig，確保 BOM 讓 Windows 編輯器正確顯示中文
    with open(OUTPUT_FILE, 'w', encoding='utf-8-sig') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f'已將結果寫入 {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
