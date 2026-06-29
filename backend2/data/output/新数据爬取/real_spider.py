#!/usr/bin/env python3
# coding: utf-8
"""
真实医疗数据爬虫 - 寻医问药网
================================================================
功能：从寻医问药网爬取真实疾病数据，格式与 medical.json 完全一致

数据源：http://jib.xywy.com
- 疾病详情页: http://jib.xywy.com/il_sii_{id}.htm
- 症状页: http://jib.xywy.com/il_sii/symptom/{id}.htm
- 检查页: http://jib.xywy.com/il_sii/inspect/{id}.htm
- 治疗页: http://jib.xywy.com/il_sii/treat/{id}.htm
- 饮食页: http://jib.xywy.com/il_sii/food/{id}.htm
- 药品页: http://jib.xywy.com/il_sii/drug/{id}.htm

用法：
  python real_spider.py --start 8809 --count 100
  python real_spider.py --start 8809 --count 500

输出：
  output/新数据爬取/new_medical.json
================================================================
"""

import os
import json
import time
import random
import argparse
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "new_medical.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class XywySpider:
    """寻医问药网爬虫"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.results = []
        self.failed_ids = []
        self.stats = {"success": 0, "failed": 0, "empty": 0}

    def fetch_page(self, url):
        """获取单个页面"""
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                return resp.content.decode('gbk', errors='ignore')
        except Exception as e:
            pass
        return None

    def parse_basic_info(self, html, disease_id):
        """解析疾病基本信息页"""
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # 疾病名称
        title = soup.find('title')
        if not title:
            return None
        name = title.text.split(',')[0].split('-')[0].strip()
        if not name or len(name) < 2:
            return None

        data = {"name": name, "_id": {"$oid": f"xywy_{disease_id}"}}

        # 简介描述
        desc_div = soup.find('div', class_='jib-articl-con')
        if desc_div:
            desc_p = desc_div.find('p')
            data['desc'] = desc_p.text.strip() if desc_p else ""

        # 分类路径
        nav_div = soup.find('div', class_='wrap mt10 nav-bar')
        if nav_div:
            category = [a.text.strip() for a in nav_div.find_all('a')]
            data['category'] = category if category else []

        # 属性信息（医保、患病比例等）
        info_divs = soup.find_all('div', class_='mt20 articl-know')
        for div in info_divs:
            p = div.find('p')
            if p:
                text = p.text.strip()
                # 解析属性
                if '医保' in text:
                    data['yibao_status'] = text.split('：')[-1].strip() if '：' in text else ""
                elif '患病比例' in text or '发病率' in text:
                    data['get_prob'] = text.split('：')[-1].strip() if '：' in text else ""
                elif '易感人群' in text:
                    data['easy_get'] = text.split('：')[-1].strip() if '：' in text else ""
                elif '传染方式' in text or '传播' in text:
                    data['get_way'] = text.split('：')[-1].strip() if '：' in text else ""
                elif '治愈率' in text:
                    data['cured_prob'] = text.split('：')[-1].strip() if '：' in text else ""
                elif '治疗周期' in text or '治疗时间' in text:
                    data['cure_lasttime'] = text.split('：')[-1].strip() if '：' in text else ""
                elif '治疗费用' in text or '费用' in text:
                    data['cost_money'] = text.split('：')[-1].strip() if '：' in text else ""
                elif '就诊科室' in text or '挂号' in text:
                    dept = text.split('：')[-1].strip() if '：' in text else ""
                    data['cure_department'] = dept.split() if dept else []
                elif '治疗方式' in text:
                    way = text.split('：')[-1].strip() if '：' in text else ""
                    data['cure_way'] = way.split() if way else []

        return data

    def fetch_symptom(self, disease_id):
        """获取症状信息"""
        url = f"http://jib.xywy.com/il_sii/symptom/{disease_id}.htm"
        html = self.fetch_page(url)
        if not html:
            return [], ""

        soup = BeautifulSoup(html, 'html.parser')

        # 症状列表
        symptoms = []
        symptom_links = soup.find_all('a', class_='gre')
        for link in symptom_links:
            text = link.text.strip()
            if text and len(text) >= 2:
                symptoms.append(text)

        # 症状详情文本（可能包含病因）
        ps = soup.find_all('p')
        detail = "\n".join(p.text.strip() for p in ps if p.text.strip())

        return symptoms, detail

    def fetch_check(self, disease_id):
        """获取检查项目"""
        url = f"http://jib.xywy.com/il_sii/inspect/{disease_id}.htm"
        html = self.fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        checks = []

        # 检查项目链接
        check_links = soup.find_all('li', class_='check-item')
        for li in check_links:
            a = li.find('a')
            if a:
                text = a.text.strip()
                if text:
                    checks.append(text)

        return checks

    def fetch_treat(self, disease_id):
        """获取治疗信息"""
        url = f"http://jib.xywy.com/il_sii/treat/{disease_id}.htm"
        html = self.fetch_page(url)
        if not html:
            return [], ""

        soup = BeautifulSoup(html, 'html.parser')

        # 治疗方式
        treat_ways = []
        ps = soup.find_all('p')
        treat_text = ""
        for p in ps:
            text = p.text.strip()
            if text:
                treat_text += text + "\n"
                # 提取治疗方式关键词
                if any(kw in text for kw in ['治疗', '手术', '药物']):
                    treat_ways.append(text.split()[0] if text.split() else text)

        return treat_ways[:5], treat_text

    def fetch_food(self, disease_id):
        """获取饮食信息"""
        url = f"http://jib.xywy.com/il_sii/food/{disease_id}.htm"
        html = self.fetch_page(url)
        if not html:
            return [], [], []

        soup = BeautifulSoup(html, 'html.parser')

        do_eat = []
        not_eat = []
        recommand_eat = []

        # 饮食分类区块
        food_divs = soup.find_all('div', class_='diet-img clearfix mt20')
        for i, div in enumerate(food_divs):
            items = [p.text.strip() for p in div.find_all('p') if p.text.strip()]
            if i == 0:
                do_eat = items
            elif i == 1:
                not_eat = items
            elif i == 2:
                recommand_eat = items

        return do_eat, not_eat, recommand_eat

    def fetch_drug(self, disease_id):
        """获取药品信息"""
        url = f"http://jib.xywy.com/il_sii/drug/{disease_id}.htm"
        html = self.fetch_page(url)
        if not html:
            return [], [], []

        soup = BeautifulSoup(html, 'html.parser')

        drugs = []
        drug_details = []

        # 药品列表
        drug_divs = soup.find_all('div', class_='fl drug-pic-rec mr30')
        for div in drug_divs:
            p = div.find('p')
            a = p.find('a') if p else None
            if a:
                drug_name = a.text.strip()
                if drug_name:
                    drugs.append(drug_name)

        # 药品详情（厂商+药品名）
        drug_links = soup.find_all('a', href=re.compile('/drug'))
        for link in drug_links:
            text = link.text.strip()
            if '(' in text:
                drug_details.append(text)

        return drugs, drug_details

    def fetch_cause_prevent(self, disease_id):
        """获取病因和预防"""
        cause_url = f"http://jib.xywy.com/il_sii/cause/{disease_id}.htm"
        prevent_url = f"http://jib.xywy.com/il_sii/prevent/{disease_id}.htm"

        cause = ""
        prevent = ""

        cause_html = self.fetch_page(cause_url)
        if cause_html:
            soup = BeautifulSoup(cause_html, 'html.parser')
            ps = soup.find_all('p')
            cause = "\n".join(p.text.strip() for p in ps if p.text.strip())

        prevent_html = self.fetch_page(prevent_url)
        if prevent_html:
            soup = BeautifulSoup(prevent_html, 'html.parser')
            ps = soup.find_all('p')
            prevent = "\n".join(p.text.strip() for p in ps if p.text.strip())

        return cause, prevent

    def fetch_disease(self, disease_id):
        """完整爬取一个疾病的所有信息"""
        try:
            # 基本信息
            basic_url = f"http://jib.xywy.com/il_sii_{disease_id}.htm"
            basic_html = self.fetch_page(basic_url)
            data = self.parse_basic_info(basic_html, disease_id)

            if not data:
                self.stats["empty"] += 1
                return None

            # 症状
            symptoms, symptom_detail = self.fetch_symptom(disease_id)
            data['symptom'] = symptoms

            # 检查
            checks = self.fetch_check(disease_id)
            data['check'] = checks

            # 治疗
            treat_ways, treat_text = self.fetch_treat(disease_id)
            if treat_ways:
                data['cure_way'] = treat_ways

            # 饮食
            do_eat, not_eat, recommand_eat = self.fetch_food(disease_id)
            data['do_eat'] = do_eat
            data['not_eat'] = not_eat
            data['recommand_eat'] = recommand_eat

            # 药品
            drugs, drug_details = self.fetch_drug(disease_id)
            data['common_drug'] = drugs
            data['recommand_drug'] = drugs  # 同一来源
            data['drug_detail'] = drug_details

            # 病因和预防
            cause, prevent = self.fetch_cause_prevent(disease_id)
            data['cause'] = cause
            data['prevent'] = prevent

            # 并发症（从症状详情中提取）
            data['acompany'] = []

            self.stats["success"] += 1
            return data

        except Exception as e:
            self.stats["failed"] += 1
            self.failed_ids.append(disease_id)
            return None

    def batch_fetch(self, start_id, count):
        """批量爬取"""
        print(f"[开始] 从ID {start_id} 开始爬取 {count} 条疾病数据")

        for i in range(count):
            disease_id = start_id + i
            print(f"[{i+1}/{count}] 爬取ID {disease_id}...", end="")

            data = self.fetch_disease(disease_id)

            if data:
                self.results.append(data)
                print(f" 成功: {data['name']}")
            else:
                print(" 失败")

            # 避免被封，随机间隔
            time.sleep(random.uniform(0.5, 1.5))

        print(f"\n[完成] 成功: {self.stats['success']}, 失败: {self.stats['failed']}, 空页: {self.stats['empty']}")

    def save(self, path=None):
        """保存结果"""
        path = path or OUTPUT_FILE
        with open(path, "w", encoding="utf-8") as f:
            for r in self.results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[保存] {len(self.results)} 条 → {path}")


def main():
    parser = argparse.ArgumentParser(description="寻医问药网数据爬虫")
    parser.add_argument("--start", type=int, default=8809, help="起始疾病ID")
    parser.add_argument("--count", type=int, default=100, help="爬取数量")
    parser.add_argument("--output", help="输出文件路径")

    args = parser.parse_args()

    print("=" * 60)
    print("寻医问药网真实数据爬虫")
    print("=" * 60)
    print(f"起始ID: {args.start}")
    print(f"爬取数量: {args.count}")
    print(f"预计时间: {args.count * 1} 秒")

    spider = XywySpider()
    spider.batch_fetch(args.start, args.count)
    spider.save(args.output)

    if spider.failed_ids:
        print(f"\n[警告] 失败ID: {spider.failed_ids}")

    print("=" * 60)
    print("完成！")


if __name__ == "__main__":
    main()