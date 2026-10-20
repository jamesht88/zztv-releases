# -*- coding: utf-8 -*-
# 源站: https://hongkongdollvideo.com
# 参考: https://raw.githubusercontent.com/Yswag/xptv-extensions/main/js/hkdoll.js

import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request

sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def getName(self):
        return "HKDoll"

    def init(self, extend):
        self.home_url = 'https://hongkongdollvideo.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.error_url = 'https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-720p.mp4'

    def getDependence(self):
        return []

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    # ── XOR decrypt helpers ───────────────────────────────────────────────────

    def _xor_dec(self, hex_str, key):
        result = []
        key_len = len(key)
        for i in range(0, len(hex_str), 2):
            byte_val = int(hex_str[i:i + 2], 16)
            key_char = key[(i // 2) % key_len]
            result.append(chr(byte_val ^ ord(key_char)))
        return ''.join(result)

    def _decode_page_params(self, param):
        key = param[-32:]
        encrypted = param[:-32]
        return json.loads(self._xor_dec(encrypted, key))

    def _md5(self, s):
        return hashlib.md5(s.encode()).hexdigest()

    def _get_play_url(self, embed_url):
        token = embed_url.split('?token=')[1]
        suffix = token[-10:]
        key = self._md5(suffix)[8:24][::-1]
        payload = token[:-10]
        decoded = self._xor_dec(payload, key)
        return json.loads(decoded)['stream']

    # ── HTTP helper ───────────────────────────────────────────────────────────

    def _encode_url(self, url):
        parts = urllib.parse.urlsplit(url)
        encoded_path = urllib.parse.quote(parts.path, safe='/:@!$&()*+,;=')
        return urllib.parse.urlunsplit((parts.scheme, parts.netloc, encoded_path, parts.query, parts.fragment))

    def api_req(self, url):
        try:
            encoded_url = self._encode_url(url)
            req = urllib.request.Request(encoded_url, headers=self.headers)
            res = urllib.request.urlopen(req, timeout=15)
            return res.read().decode('utf-8')
        except Exception:
            return 'False'

    # ── 解析 video-item 列表（共用）────────────────────────────────────────────

    def _parse_video_list(self, root):
        """
        HTML 结构:
        <div class="video-item">
          <div class="thumb">
            <a href="...完整URL..." title="标题">
              <img data-src="...真实图片..." src="base64占位">
            </a>
          </div>
        </div>
        图片用懒加载，真实地址在 data-src，不是 src。
        """
        video_list = []
        for item in root.xpath('//div[@class="video-item"]'):
            # href 和 title 在 .thumb a
            hrefs  = item.xpath('.//div[@class="thumb"]/a/@href')
            titles = item.xpath('.//div[@class="thumb"]/a/@title')
            # 图片：懒加载用 data-src，首屏第一张可能直接用 src
            covers = item.xpath('.//div[@class="thumb"]//img/@data-src')
            if not covers:
                covers = [s for s in item.xpath('.//div[@class="thumb"]//img/@src') if not s.startswith('data:')]
            # 时长在 .duration（原 JS 用 .duratio，网页实际 class 是 duration）
            durs   = item.xpath('.//div[@class="duration"]/text()')
            if not durs:
                durs = item.xpath('.//*[contains(@class,"duratio")]/text()')

            href = hrefs[0] if hrefs else ''
            if not href:
                continue
            # 补全相对路径图片 URL
            cover = covers[0] if covers else ''
            if cover and cover.startswith('/'):
                cover = self.home_url + cover
            video_list.append({
                'vod_id':      href,
                'vod_name':    titles[0].strip() if titles else '',
                'vod_pic':     cover,
                'vod_remarks': durs[0].strip() if durs else '',
            })
        return video_list

    # ── Spider methods ────────────────────────────────────────────────────────

    def homeContent(self, filter):
        """
        分类来自左侧 <ul class="menu"> 内的 <a class="menu-link">
        href 是完整 URL，例如 https://hongkongdollvideo.com/麻豆传媒映画/
        忽略 cnporn.net 等外链，只保留本站链接
        """
        from lxml import etree
        res = self.api_req(self.home_url)
        if res == 'False':
            return {'class': [], 'filters': {}}

        root = etree.HTML(res)
        classes = []

        seen = set()
        # 从 ul.menu 抓所有 a.menu-link，只保留本站链接
        for a in root.xpath('//ul[@class="menu"]//a[@class="menu-link"]'):
            name = (a.text or '').strip()
            href = a.get('href', '')
            if not name or not href:
                continue
            if self.home_url not in href:
                continue   # 跳过外链（如 cnporn.net）
            if href in seen:
                continue   # 去重
            seen.add(href)
            # 把"最新"改显示为"推荐"
            if '/latest/' in href:
                name = '推荐'
            classes.append({'type_id': href, 'type_name': name})

        return {'class': classes, 'filters': {}}

    def homeVideoContent(self):
        return {'list': [], 'parse': 0, 'jx': 0}

    def categoryContent(self, cid, page, filter, ext):
        """
        分页 URL 规则：
          第1页：https://hongkongdollvideo.com/麻豆传媒映画/
          第2页：https://hongkongdollvideo.com/麻豆传媒映画/2.html
        """
        from lxml import etree

        url = cid.rstrip('/')
        if int(page) > 1:
            url = url + '/' + str(page) + '.html'
        else:
            url = url + '/'

        res = self.api_req(url)
        if res == 'False':
            return {'list': [], 'parse': 0, 'jx': 0}

        root = etree.HTML(res)
        video_list = self._parse_video_list(root)
        return {'list': video_list, 'parse': 0, 'jx': 0}

    def detailContent(self, did):
        ids = did[0]
        # vod_id 是完整 URL
        url = ids if ids.startswith('http') else self.home_url + ids

        res = self.api_req(url)
        if res == 'False':
            return {'list': [], 'parse': 0, 'jx': 0}

        play_url = self.error_url
        try:
            m = re.search(r'var __PAGE__PARAMS__="([^"]+)"', res)
            if m:
                page_data = self._decode_page_params(m.group(1))
                embed_url = page_data['player']['embedUrl']
                play_url = self._get_play_url(embed_url)
        except Exception as e:
            print(f'[hkdoll] detailContent error: {e}')

        vod = {
            'type_name':    '',
            'vod_id':       ids,
            'vod_name':     '',
            'vod_remarks':  '',
            'vod_year':     '',
            'vod_area':     '',
            'vod_actor':    '',
            'vod_director': '',
            'vod_content':  '',
            'vod_play_from': 'HKDoll',
            # 用 ||| 把 play_url 和 page_url 一起传给 playerContent
            'vod_play_url': f'播放${play_url}|||{url}',
        }
        return {'list': [vod], 'parse': 0, 'jx': 0}

    def playerContent(self, flag, pid, vipFlags):
        if '|||' in pid:
            play_url, page_url = pid.split('|||', 1)
        else:
            play_url = pid
            page_url = self.home_url

        return {
            'url': play_url,
            'header': {
                'User-Agent': self.headers['User-Agent'],
                'Referer': page_url,
            },
            'parse': 0,
            'jx': 0,
        }

    def searchContent(self, key, quick, page='1'):
        from lxml import etree
        pg = int(page) if page else 1
        encoded = urllib.parse.quote(key)
        # 搜索 URL：/search/关键词  或  /search/关键词/2.html
        if pg > 1:
            url = f'{self.home_url}/search/{encoded}/{pg}.html'
        else:
            url = f'{self.home_url}/search/{encoded}'

        res = self.api_req(url)
        if res == 'False':
            return {'list': [], 'parse': 0, 'jx': 0}

        root = etree.HTML(res)
        video_list = self._parse_video_list(root)
        return {'list': video_list, 'parse': 0, 'jx': 0}

    def localProxy(self, params):
        pass

    def destroy(self):
        return '正在Destroy'


if __name__ == '__main__':
    pass
