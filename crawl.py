import time
import re
import os
import requests
from lxml import etree
from tqdm import tqdm

if __name__ == '__main__':
    cookie = "uuid=eyJpdiI6InQrMUdvaXVwbGUwaGg4VE9VU0MzYUE9PSIsInZhbHVlIjoidDNJZWdGU0pqdm9sWGhrY1FycG9cL3pid3cxaEp4blVhWVZUQ2JGNzRhQ2tjaENRV3g0cW5YSk82aUVIYXBQMUYiLCJtYWMiOiI4MmFjMDcxMThmMTgzMGIxZGM1M2UwODAwZWI2NGY0YjdhN2M1NTRiMDc2YjE0NDRlNTVkY2QxZTc1NWVkYTJjIn0%3D; userId=220632; acw_tc=2760820917212323837874530e1d79c6c16f15bc2bb5520b14b9aa9e947ea9; Hm_lvt_0bd5902d44e80b78cb1cd01ca0e85f4a=1721142431,1721143321,1721232391; HMACCOUNT=D263DB9A03DE3735; Hm_lvt_0449d831efe3131221f6d2f2b6c91897=1721142431,1721143321,1721232401; payment_from=eyJpdiI6ImV3MXpcL2VmQzRMZEVmOUUyWm5PbHB3PT0iLCJ2YWx1ZSI6IkhJWVg1UlFKSVNyRTVLNG1cL3YySldRPT0iLCJtYWMiOiI0NGUzYmJmYzBiNDRkNWI3NDhmYzNjNzIwMDc0ZGNjZjg1NjQ0MGMwN2I3YTgyZTcyYjg5NjdkNDVmNDEyMWMxIn0%3D; counter=eyJpdiI6ImhQT1FYc2FDbWlvd2lcL1wvYWZoUW5xdz09IiwidmFsdWUiOiJmNVkweU4yeTduNFdDaDBGbWMwOFR3PT0iLCJtYWMiOiIwYTI3OTliYmIyYTNkMjFkOTExNGI1NDhmZWFlOTRmNDM0ODkzODJiYzZmODAxMjM4YmRjNGEyNzIwYzBhZWQ5In0%3D; Hm_lpvt_0bd5902d44e80b78cb1cd01ca0e85f4a=1721232504; Hm_lpvt_0449d831efe3131221f6d2f2b6c91897=1721232504; gzr_session=eyJpdiI6IlFKS0ZFaUVKYXhXVDgxUzBkbkdOY3c9PSIsInZhbHVlIjoiYStnWHBwaFF6d2tmYkFZOHRSV3dOWkdkUWp5cHQ3Wmw4U0ZqS1kwTnN2XC9lM0FCN2ZIQmZWRkxaTHlZVit2djciLCJtYWMiOiI1ZTZhMGY5YmNiYTU4Mjg3ZDE0Y2I2Nzc3MDIxNDE1OTVmZDBlNzNhYjVjZjFiYjZiNzBmOWZmMzk0NDY3MTRmIn0%3D"
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
    headers = {'User_Agent': user_agent, 'Cookie': cookie}

    url = f"https://www.izaiwen.cn/pro/"
    resp = requests.get(url, headers=headers)
    time.sleep(0.5)
    resp.encoding = 'utf-8'
    tree = etree.HTML(resp.text)
    # 提取项目分类
    funding_type_id_list = tree.xpath('//div[@id="funding_type_list"]//span[@class="class "]//a/@href')
    funding_type_name_list = tree.xpath('//div[@id="funding_type_list"]//span[@class="class "]//a/text()')
    # 存储项目分类
    os.makedirs('../type_lst', exist_ok=True)
    for id, name in zip(funding_type_id_list, funding_type_name_list):
        real_id = re.findall(r'/pro/(.*)',id)[0].strip()
        with open('../type_lst/funding_type.csv', mode='a', encoding='utf-8_sig') as f:
            f.write(f'{real_id}|{name.strip()}\n')
    # 提取一级学科分类
    subject1_id_list = tree.xpath('//div[@class="filter-content-father content-box level1 y-hide-box"]//span[@class="class "]//a/@href')
    subject1_name_list = tree.xpath('//div[@class="filter-content-father content-box level1 y-hide-box"]//span[@class="class "]//a/text()')
    # 存储一级学科分类
    for id, name in zip(subject1_id_list, subject1_name_list):
        real_id = re.findall(r'/pro/(.*)',id)[0].strip()
        with open('../type_lst/subject1.csv', mode='a', encoding='utf-8_sig') as f:
            f.write(f'{real_id}|{name.strip()}\n')
    # 提取二级学科分类
    error = []
    for subject_url in tqdm(subject1_id_list[1:], desc='crawl_subject2', total=len(subject1_id_list[1:])):
        resp = requests.get(subject_url, headers=headers)
        time.sleep(0.5)
        if resp.status_code == 200:
            resp.encoding = 'utf-8'
            tree = etree.HTML(resp.text)
            # 提取二级学科分类
            subject2_id_list = tree.xpath('//div[@class="filter-content-children content-box level2"]//span[@class="class "]//a/@href')
            subject2_name_list = tree.xpath('//div[@class="filter-content-children content-box level2"]//span[@class="class "]//a/text()')
            for id, name in zip(subject2_id_list, subject2_name_list):
                real_id = re.findall(r'/pro/(.*)', id)[0].strip()
                with open('../type_lst/subject2.csv', mode='a', encoding='utf-8_sig') as f:
                    f.write(f'{real_id}|{name.strip()}\n')
        else:
            error.append(subject_url)
    print(error)


