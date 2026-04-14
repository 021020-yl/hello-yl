import requests
from lxml import etree
import os
import time
import csv

START_URL = "https://oatd.org/oatd/search?q=AI&form=basic&pubdate.facet=2022"
TARGET_COUNT = 10
SAVE_DIR = "oatd_ai_papers"

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://oatd.org/oatd/search?q=AI&form=basic',
    'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Microsoft Edge";v="146"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version': '"146.0.3856.109"',
    'sec-ch-ua-full-version-list': '"Chromium";v="146.0.7680.179", "Not-A.Brand";v="24.0.0.0", "Microsoft Edge";v="146.0.3856.109"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"19.0.0"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0'
}

COOKIES = {
    '__utma': '27275938.2074884647.1776093217.1776093217.1776093217.1',
    '__utmc': '27275938',
    '__utmz': '27275938.1776093217.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
    '_pk_id.4.c2fb': '2dff56a7d1f64c11.1776093683.',
    '_pk_ses.4.c2fb': '1',
    'cf_clearance': 'Oxxmq1LJlGrZ2LufSJCM21TQmvuVOUv_4Nj7KOZ.1no-1776101409-1.2.1.1-OxRYFoUfoOOeby.PAEsg46HXdtRT_Fc059YBGBN19pspaM1gx3blbtS5cbH4snKeduPM_sVvCsGOPHDAxz3oJxxcmJ0uKy2fc23Z7TjbULf47ugQVTJHV0f5uLYBXV_OSggtiF6c190XFLYwIBlfxOSEwOYNl8hjabK8tVWsFAffmeHC0zDQ6MlasrGKNe8OMojTO7rKB8qRQ16WLLSywqJ2s7dkZzZta5LGBkVu2wueMV1AeCLf_OSudETNXzaDdRd55r8AG.BDyfkjD30oUy3tXRI8uZ1kBenAIDDhvrhN9GpoA.iZYNNff2Iep162QMBAOccTly796B5UL62vfg'
}
os.makedirs(SAVE_DIR, exist_ok=True)

def download_pdf(pdf_url, title):
    if not pdf_url:
        return "无PDF链接"
    try:
        filename = "".join(c for c in title if c.isalnum() or c in (' ', '_')).strip()[:50] + ".pdf"
        filepath = os.path.join(SAVE_DIR, filename)
        resp = requests.get(pdf_url, headers=HEADERS, cookies=COOKIES, timeout=30, stream=True)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(1024*1024):
                f.write(chunk)
        print(f"[OK] PDF下载成功: {filename}")
        return filepath
    except Exception as e:
        print(f"[ERR] PDF下载失败: {str(e)[:50]}")
        return None

def main():
    all_data = []
    page = 1
    print("=" * 50)
    print("开始爬取 OATD 论文（优先筛选可下载PDF的论文）")
    print("=" * 50)

    while len(all_data) < TARGET_COUNT:
        print(f"\n===== 第 {page} 页 | 已收集 {len(all_data)}/{TARGET_COUNT} 条 =====")
        current_search_url = f"{START_URL}&page={page}"

        try:
            search_resp = requests.get(current_search_url, headers=HEADERS, cookies=COOKIES, timeout=15)
            print(f"[INFO] 搜索页状态码: {search_resp.status_code}")
            if search_resp.status_code != 200:
                print("[ERR] 搜索页访问失败！可能被反爬拦截")
                break

            search_tree = etree.HTML(search_resp.text)
            relative_hrefs = search_tree.xpath('//p[@class="shareIcon"]//a/@href')
            base_url = "https://oatd.org/oatd/"
            record_urls = [base_url + href for href in relative_hrefs]
            print(f"[INFO] 本页获取记录详情链接数: {len(record_urls)}")

            if not record_urls:
                print("[WARN] 无记录详情链接，爬取结束")
                break

        except Exception as e:
            print(f"[ERR] 搜索页请求失败: {str(e)[:50]}")
            break

        for record_url in record_urls:
            if len(all_data) >= TARGET_COUNT:
                break

            try:
                # ========== 步骤1：访问记录详情页，获取真正的详情页URL ==========
                print(f"\n[->] 访问记录详情页: {record_url[:80]}...")

                record_resp = requests.get(record_url, headers=HEADERS, cookies=COOKIES, timeout=15)
                print(f"记录详情页状态码: {record_resp.status_code}")
                if record_resp.status_code != 200:
                    print("[SKIP] 记录详情页访问失败，跳过")
                    continue

                record_tree = etree.HTML(record_resp.text)

                real_detail_candidates = record_tree.xpath('//td[@itemprop="url"]//a/@href')
                real_detail_url = real_detail_candidates[0].strip() if real_detail_candidates else ""
                
                if not real_detail_url:
                    print("[SKIP] 未找到真正的详情页URL，跳过")
                    continue

                # ========== 步骤2：访问真正的详情页，优先检查PDF URL ==========
                detail_resp = requests.get(real_detail_url, headers=HEADERS, cookies=COOKIES, timeout=15)
                print(f"真正详情页状态码: {detail_resp.status_code}")
                if detail_resp.status_code != 200:
                    print("[SKIP] 真正详情页访问失败，跳过")
                    continue

                detail_tree = etree.HTML(detail_resp.text)
                pdf_url_list = detail_tree.xpath('//span[@class="ep_document_citation"]/a/@href')
                pdf_url = pdf_url_list[0].strip() if pdf_url_list else ""

                # 核心判断：没有PDF URL直接跳过
                if not pdf_url:
                    print("[SKIP] 无PDF URL，跳过此论文")
                    continue
                
                print(f"[OK] 发现PDF URL: {pdf_url[:60]}...")

                # ========== 步骤3：确认有PDF后，从记录详情页提取字段信息 ==========
                title = ''.join(record_tree.xpath('//div[@class="resultWrapper"]//td[@itemprop="name"]/text()')).strip()
                author = '; '.join(record_tree.xpath('//td[@itemprop="author"]/span[@itemprop="author"]/text()')).strip()
                university = ''.join(record_tree.xpath('//td[@itemprop="publisher"]/text()')).strip()
                publish_year = ''.join(record_tree.xpath('//td[@itemprop="datePublished"]/text()')).strip()
                abstract = ''.join(record_tree.xpath('//td[@itemprop="description"]/text()')).strip()

                print(f"[DATA] 标题={title[:30]}... | 作者={author or '空'}")

                # 下载PDF
                pdf_path = download_pdf(pdf_url, title)

                paper_data = {
                    "编号": len(all_data) + 1,
                    "标题": title,
                    "作者": author,
                    "学位授予机构": university,
                    "年份": publish_year,
                    "摘要": abstract,
                    "记录详情URL": record_url,
                    "详情页URL": real_detail_url,
                    "PDF URL": pdf_url,
                    "本地保存路径": pdf_path
                }
                all_data.append(paper_data)
                print(f"[OK] 已保存第 {len(all_data)} 条数据（含PDF）")
                time.sleep(1.5)

            except Exception as e:
                print(f"[ERR] 单条数据失败: {str(e)[:60]}")
                continue

        page += 1
        time.sleep(2)

    if all_data:
        with open("oatd_ai_papers.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
            writer.writeheader()
            writer.writerows(all_data)
        print(f"\n[DONE] 爬取完成！总数据：{len(all_data)} 条 | 已保存 CSV")
    else:
        print("\n[ERR] 未爬取到任何数据！")

if __name__ == "__main__":
    main()
