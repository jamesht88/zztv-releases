# -*- coding: utf-8 -*-
import re
import sys
import urllib.request
import urllib.parse
from lxml import etree

sys.path.append('..')
try:
    from base.spider import Spider
except Exception:
    class Spider:
        pass


class Spider(Spider):

    def getName(self):
        return "MissAV"

    def init(self, extend=""):
        self.domains = [
            "https://missav.live",
            "https://missav123.com",
            "https://missav.online",
            "https://missav.ws",
            "https://missav.ai"
        ]
        self.home_url = self.domains[0]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": f"{self.home_url}/",
            "Connection": "keep-alive"
        }
        self.error_url = "https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-720p.mp4"

    def getDependence(self):
        return ['lxml']

    def isVideoFormat(self, url):
        pass

    def homeContent(self, filter=False):
        return {
            'class': [
                {'type_id': '/dm45', 'type_name': 'Home'},
                {'type_id': '/dm265/chinese-subtitle', 'type_name': '🀄 中文字幕'},
                {'type_id': '/dm514/new', 'type_name': '⚡ 最近更新'},
                {'type_id': '/dm588/release', 'type_name': '🎬 新作上市'},
                {'type_id': '/dm621/uncensored-leak', 'type_name': '💧 无码流出'},
                {'type_id': '/actresses', 'type_name': '👠 女优一览'},
                {'type_id': '/actresses/ranking', 'type_name': '🏆 女优排行'},
                {'type_id': '/genres', 'type_name': '🏷️ 全部类型'},
                {'type_id': '/makers', 'type_name': '🏢 全部发行商'},
                {'type_id': '/genres/VR', 'type_name': '🥽 VR 专区'},
                {'type_id': '/dm291/today-hot', 'type_name': '📅 今日热门'},
                {'type_id': '/dm169/weekly-hot', 'type_name': '📈 本周热门'},
                {'type_id': '/dm257/monthly-hot', 'type_name': '👑 本月热门'},
                {'type_id': '/dm99/fc2', 'type_name': '💎 FC2'},
                {'type_id': '/dm319995/heyzo', 'type_name': '💎 HEYZO'},
                {'type_id': '/dm29/tokyohot', 'type_name': '💎 东京热'},
                {'type_id': '/dm695579/1pondo', 'type_name': '💎 一本道'},
                {'type_id': '/dm1271239/caribbeancom', 'type_name': '💎 加勒比'},
                {'type_id': '/dm14081/caribbeancompr', 'type_name': '💎 加勒比PR'},
                {'type_id': '/dm1117248/10musume', 'type_name': '💎 天然素人'},
                {'type_id': '/dm370414/pacopacomama', 'type_name': '💎 熟女俱乐部'},
                {'type_id': '/dm135/gachinco', 'type_name': '💎 Gachinco'},
            ],
            'filters': {}
        }

    def homeVideoContent(self):
        video_list = []
        res = self.api_req(f'{self.home_url}/dm45')
        if not res or res == 'False':
            return {'list': [], 'parse': 0, 'jx': 0}

        try:
            root = etree.HTML(res)
            data_list = root.xpath('//div[contains(@class,"thumbnail group")]')
            for i in data_list:
                names = i.xpath('./div[2]/a/text()')
                if len(names) > 0:
                    name = names[0].strip()
                    if len(name) > 0:
                        href = i.xpath('./div[2]/a/@href')[0].replace(self.home_url, '')
                        pics = i.xpath('./div[1]/a/img/@data-src') or i.xpath('./div[1]/a/img/@src')
                        pic = pics[0] if pics else ''
                        video_list.append({
                            'vod_id': href,
                            'vod_name': name,
                            'vod_pic': pic,
                            'vod_remarks': '',
                            'style': {'type': 'rect', 'ratio': 1.5}
                        })
        except Exception:
            pass

        return {
            'list': video_list,
            'parse': 0,
            'jx': 0
        }

    def categoryContent(self, cid, page=1, filter=False, ext=""):
        video_list = []
        cid = str(cid or "").strip()
        page = str(page or 1)

        # 1. 🏷️ 全部类型 (/genres)
        if cid == '/genres':
            res = self.api_req(f'{self.home_url}/genres')
            if res and res != 'False':
                try:
                    root = etree.HTML(res)
                    items = root.xpath('//a[contains(@href, "/genres/")]')
                    seen = set()
                    for a in items:
                        href = a.xpath('./@href')[0]
                        texts = [t.strip() for t in a.xpath('.//text()') if t.strip()]
                        if not texts:
                            continue
                        name = texts[0]
                        count = texts[1] if len(texts) > 1 else ""
                        path = re.sub(r'^https?://[^/]+', '', href)
                        if path not in seen and name not in seen:
                            seen.add(path)
                            seen.add(name)
                            video_list.append({
                                'vod_id': path,
                                'vod_name': name,
                                'vod_pic': 'https://img.icons8.com/?size=256w&id=42799&format=png',
                                'vod_remarks': count,
                                'vod_tag': 'folder',
                                'style': {'type': 'rect', 'ratio': 1.33}
                            })
                except Exception:
                    pass
            return {'list': video_list, 'parse': 0, 'jx': 0}

        # 2. 🏢 全部发行商 (/makers)
        if cid == '/makers':
            res = self.api_req(f'{self.home_url}/makers')
            if res and res != 'False':
                try:
                    root = etree.HTML(res)
                    items = root.xpath('//a[contains(@href, "/makers/")]')
                    seen = set()
                    for a in items:
                        href = a.xpath('./@href')[0]
                        texts = [t.strip() for t in a.xpath('.//text()') if t.strip()]
                        if not texts:
                            continue
                        name = texts[0]
                        count = texts[1] if len(texts) > 1 else ""
                        path = re.sub(r'^https?://[^/]+', '', href)
                        if path not in seen and name not in seen:
                            seen.add(path)
                            seen.add(name)
                            video_list.append({
                                'vod_id': path,
                                'vod_name': name,
                                'vod_pic': 'https://img.icons8.com/?size=256w&id=12140&format=png',
                                'vod_remarks': count,
                                'vod_tag': 'folder',
                                'style': {'type': 'rect', 'ratio': 1.33}
                            })
                except Exception:
                    pass
            return {'list': video_list, 'parse': 0, 'jx': 0}

        # 3. 👠 女优一览与排行 (/actresses, /actresses/ranking)
        if cid in ('/actresses', '/actresses/ranking'):
            res = self.api_req(f'{self.home_url}{cid}?page={page}')
            if res and res != 'False':
                try:
                    root = etree.HTML(res)
                    data_list = root.xpath('//div[contains(@class,"space-y-4")]')
                    for i in data_list:
                        names = i.xpath('./div/a/h4/text()')
                        if len(names) > 0:
                            name = names[0].strip()
                            href = i.xpath('./div/a/@href')[0].replace(self.home_url, '')
                            pics = i.xpath('./a/div/img/@src') or i.xpath('./a/div/img/@data-src')
                            pic = pics[0] if len(pics) > 0 else 'https://img.icons8.com/?size=256w&id=l24cyKyOwOjt&format=png'
                            video_list.append({
                                'vod_id': href,
                                'vod_name': name,
                                'vod_pic': pic,
                                'vod_remarks': '',
                                'vod_tag': 'folder',
                                'style': {'type': 'oval'}
                            })
                except Exception:
                    pass
            return {'list': video_list, 'parse': 0, 'jx': 0}

        # 4. 普通影视列表 (中文字幕, 新作, 热门, 单一发行商, 单一类型等)
        sep = '&' if '?' in cid else '?'
        req_url = f'{self.home_url}{cid}{sep}page={page}'
        res = self.api_req(req_url)
        if not res or res == 'False':
            return {'list': [], 'parse': 0, 'jx': 0}

        try:
            root = etree.HTML(res)
            data_list = root.xpath('//div[contains(@class,"thumbnail group")]')
            for i in data_list:
                names = i.xpath('./div[2]/a/text()')
                if len(names) > 0:
                    name = names[0].strip()
                    if len(name) > 0:
                        href = i.xpath('./div[2]/a/@href')[0].replace(self.home_url, '')
                        pics = i.xpath('./div[1]/a/img/@data-src') or i.xpath('./div[1]/a/img/@src')
                        pic = pics[0] if len(pics) > 0 else ''
                        video_list.append({
                            'vod_id': href,
                            'vod_name': name,
                            'vod_pic': pic,
                            'vod_remarks': '',
                            'style': {'type': 'rect', 'ratio': 1.5}
                        })
        except Exception:
            pass

        return {'list': video_list, 'parse': 0, 'jx': 0}

    def detailContent(self, did):
        ids = did[0] if isinstance(did, (list, tuple)) else did
        page_url = f'{self.home_url}{ids}' if ids.startswith('/') else f'{self.home_url}/{ids}'
        res = self.api_req(page_url)
        if not res or res == 'False':
            return {'list': [], 'parse': 0, 'jx': 0}

        datas = re.findall(r'm3u8(.*?)com', res)
        if len(datas) > 0:
            b = datas[0].split('|')[1:-1]
            b.reverse()
            b = '-'.join(b)
            m3u8_url = f"https://surrit.com/{b}/playlist.m3u8"
        else:
            m3u8_url = self.error_url

        pid = f"{m3u8_url}|||{page_url}"

        video_list = [{
            'type_name': '',
            'vod_id': ids,
            'vod_name': '',
            'vod_remarks': '',
            'vod_year': '',
            'vod_area': '',
            'vod_actor': '',
            'vod_director': '',
            'vod_content': '',
            'vod_play_from': 'MissAV',
            'vod_play_url': f'01${pid}'
        }]
        return {"list": video_list, 'parse': 0, 'jx': 0}

    def searchContent(self, key, quick, page='1'):
        wd = urllib.parse.quote(key)
        video_list = []
        res = self.api_req(f'{self.home_url}/search/{wd}?page={page}')
        if not res or res == 'False':
            return {'list': [], 'parse': 0, 'jx': 0}

        try:
            root = etree.HTML(res)
            data_list = root.xpath('//div[contains(@class,"thumbnail group")]')
            for i in data_list:
                names = i.xpath('./div[2]/a/text()')
                if len(names) > 0:
                    name = names[0].strip()
                    if len(name) > 0:
                        href = i.xpath('./div[2]/a/@href')[0].replace(self.home_url, '')
                        pics = i.xpath('./div[1]/a/img/@data-src') or i.xpath('./div[1]/a/img/@src')
                        pic = pics[0] if len(pics) > 0 else ''
                        video_list.append({
                            'vod_id': href,
                            'vod_name': name,
                            'vod_pic': pic,
                            'vod_remarks': '',
                            'style': {'type': 'rect', 'ratio': 1.5}
                        })
        except Exception:
            pass

        return {
            'list': video_list,
            'parse': 0,
            'jx': 0
        }

    def playerContent(self, flag, pid, vipFlags):
        if '|||' in pid:
            m3u8_url, page_url = pid.split('|||', 1)
        else:
            m3u8_url = pid
            page_url = self.home_url

        h2 = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
            "Referer": page_url,
        }
        return {"url": m3u8_url, "header": h2, "parse": 0, "jx": 0}

    def localProxy(self, params):
        pass

    def destroy(self):
        return '正在Destroy'

    def api_req(self, url):
        # 多域名轮询容灾
        for domain in self.domains:
            # 替换当前测试域名
            target_url = url
            for d in self.domains:
                if target_url.startswith(d):
                    target_url = target_url.replace(d, domain)
                    break
            if not target_url.startswith('http'):
                target_url = f"{domain}{target_url}"

            req_headers = dict(self.headers)
            req_headers['Referer'] = f"{domain}/"

            try:
                request = urllib.request.Request(target_url, headers=req_headers)
                response = urllib.request.urlopen(request, timeout=8)
                if response.status == 200:
                    data = response.read().decode('utf-8', errors='ignore')
                    if data and 'Just a moment...' not in data:
                        self.home_url = domain
                        return data
            except Exception:
                continue

        return 'False'


if __name__ == '__main__':
    s = Spider()
    s.init("")
    print("Categories:", len(s.homeContent(False)['class']))
