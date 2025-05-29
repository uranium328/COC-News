#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import xml.etree.ElementTree as ET
import os
import re
from urllib.parse import unquote

# === 設定 ===
SITEMAP_INDEX_URL = 'https://supercell.com/sitemap.xml'
NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
BLOG_PATH_KEYWORD = '/en/games/clashofclans/zh/blog/'
DATA_FILE = 'known_articles.json'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; MyCrawler/1.0; +https://example.com/bot)'
}

# === 功能 ===

def fetch_sitemap_urls():
    resp = requests.get(SITEMAP_INDEX_URL, headers=HEADERS)
    resp.raise_for_status()
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

def classify_article(url):
    slug = unquote(url.rstrip('/').split('/')[-1].lower())
    if re.match(r'^2025-\d{1,2}-', slug):
        return '活動獎勵'
    return '公告'

def load_known_articles():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding='utf-8-sig') as f:
            return json.load(f)
    return []

def save_known_articles(articles):
    with open(DATA_FILE, 'w', encoding='utf-8-sig') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

# === 主流程 ===

def main():
    sitemap_urls = fetch_sitemap_urls()

    all_urls = set()
    for sm_url in sitemap_urls:
        all_urls.update(fetch_blog_urls(sm_url))
    all_urls = sorted(all_urls)

    known_articles = load_known_articles()
    known_urls = set(a['url'] for a in known_articles)

    new_articles = []
    for url in all_urls:
        if url not in known_urls:
            category = classify_article(url)
            print(f'【新文章】[{category}] - {url}')
            new_articles.append({'url': url, 'category': category})

    if new_articles:
        print(f'\n共發現 {len(new_articles)} 篇新文章！')
        result = known_articles + new_articles
    else:
        print('沒有新文章。')
        result = known_articles

    save_known_articles(result)

    # 給 N8N 輸出使用
    print(json.dumps({
        'new_articles': new_articles
    }, ensure_ascii=False))

if __name__ == '__main__':
    main()
