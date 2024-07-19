import time
import os
import requests
from lxml import etree
from urllib.parse import urljoin
import json


stops_space = (
        ' '
        '\xa0'  # 空格:不间断空白符 &nbsp(non-breaking space)，
        '\u3000'  # 顶格 
        '\u2002'  # 空格
        '\u2003'  # 2空格
        '\u3000',
        '\n')  # '\|'


def remove_stops_space(input_string):
    # 创建转换表，将这些字符映射到 None
    translation_table = str.maketrans('', '', ''.join(stops_space))
    # 使用 translate 方法移除这些字符
    return input_string.translate(translation_table)


def show_files(path, all_files):
    file_list = os.listdir(path)
    for f in file_list:
        cur_path = os.path.join(path, f)
        if os.path.isdir(cur_path):
            show_files(cur_path, all_files)
        else:
            all_files.append(cur_path)
    return all_files


def is_last_folder_in_directory(path):
    if os.path.isdir(folder_path):
        # 获取文件路径的父目录
        parent_dir = os.path.dirname(path)

        # 获取父目录中的所有文件夹
        all_folders = [name for name in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, name))]

        # 按名称升序排列文件夹
        all_folders.sort()

        # 获取当前文件夹的名称
        current_folder = os.path.basename(path)

        # 检查当前文件夹是否是最后一个文件夹
        return all_folders[-1] == current_folder
    else:
        return False


if __name__ == '__main__':
    with open('../type_lst/funding_type.csv', mode='r', encoding='utf-8_sig') as f:
        funding_type_lst = f.readlines()
    funding_type_dict = {}
    for item in funding_type_lst:
        lst = item.strip().split('|')
        funding_type_dict[lst[0]] = lst[1]

    with open('../type_lst/subject2.csv', mode='r', encoding='utf-8_sig') as f:
        subject2_lst = f.readlines()
    subject2_dict = {}
    for item in subject2_lst:
        lst = item.strip().split('|')
        subject2_dict[lst[0]] = lst[1]


    cookie = "uuid=eyJpdiI6InQrMUdvaXVwbGUwaGg4VE9VU0MzYUE9PSIsInZhbHVlIjoidDNJZWdGU0pqdm9sWGhrY1FycG9cL3pid3cxaEp4blVhWVZUQ2JGNzRhQ2tjaENRV3g0cW5YSk82aUVIYXBQMUYiLCJtYWMiOiI4MmFjMDcxMThmMTgzMGIxZGM1M2UwODAwZWI2NGY0YjdhN2M1NTRiMDc2YjE0NDRlNTVkY2QxZTc1NWVkYTJjIn0%3D; userId=220632; _c_WBKFRo=E9jtIyOZHqvt5Ci1nVWZ7rabgn6OvSd11e6crE2E; acw_tc=7b39758517213674129416377e53d667d2e6fbd58143c4f3bf1f7b473e7a08; Hm_lvt_0449d831efe3131221f6d2f2b6c91897=1721265098,1721285873,1721289158,1721367420; HMACCOUNT=D263DB9A03DE3735; Hm_lvt_0bd5902d44e80b78cb1cd01ca0e85f4a=1721285364,1721285874,1721289158,1721367420; counter=eyJpdiI6IjVDb2orTVVSRUdWQk1NOTljMDF0Z1E9PSIsInZhbHVlIjoiakQ3cWwrcGUwREUxOGpzQkxRTVRQZz09IiwibWFjIjoiN2E4ZTdhYjkwOTQwMTU2OGYwY2EyNmQ3YTlkZTI4MjcyNjEzZTExY2QxZDZjOTZhNjljNjlhZjdhYTUzYTVlMyJ9; Hm_lpvt_0449d831efe3131221f6d2f2b6c91897=1721367743; Hm_lpvt_0bd5902d44e80b78cb1cd01ca0e85f4a=1721367743; gzr_session=eyJpdiI6InJXbzNlcDVRSDZNV0l3RVdncGl4MFE9PSIsInZhbHVlIjoiODdoR3lIeXUrdE93MnNrXC84Y0liUmMxbHJpWlJhc2JlcHFpYXN1UGFNTlV6bDJNVUU4dmdWUzdMVXU1bjladHAiLCJtYWMiOiIyOTUzZjUzZGQwNmYyNjdiOTc3YTVjNmExOTQyZTdlNjI3MmIyZDE2ZDVkMzY1MDNmYzE3ODNhZmI5NzFmMjIxIn0%3D"
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
    headers = {'User_Agent': user_agent, 'Cookie': cookie}

    for year in range(2019, 2024):
        for funding_type in funding_type_dict:
            for subject2 in subject2_dict:
                folder_path = f'../data/{year}/{funding_type_dict[funding_type]}/{subject2_dict[subject2]}'
                if (os.path.isdir(folder_path) == False) or (is_last_folder_in_directory(folder_path) == True):
                    os.makedirs(folder_path, exist_ok=True)
                    try:
                        url = f"https://www.izaiwen.cn/pro/{funding_type}-{subject2}"
                        params = {'sy': year, 'ey': year}
                        resp = requests.get(url, headers=headers, params=params)
                        time.sleep(0.5)
                        resp.encoding = 'utf-8'
                        tree = etree.HTML(resp.text)
                        access_exception = tree.xpath('//h1//text()')
                        if (resp.status_code == 200) & (access_exception[0] != '访问异常，请稍后再试~ '):
                            # 提取查询总数
                            results_num = tree.xpath('//blockquote[@class="m-t-34 m-b-25 total-result"]//span[@class="num"]/text()')
                            if (results_num is None) or (len(results_num) == 0):
                                with open('../data/error.txt', mode='a', encoding='utf-8_sig') as error_f:
                                    error_f.write(f'{url}\n')
                                time.sleep(360)
                            else:
                                results_num_real = int(results_num[0].strip())
                                if results_num_real <= 5000:
                                    page_num = tree.xpath('//li[@class="page-item"]/a/text()')
                                    final_page = int(page_num[-2])
                                    for page in range(1, final_page+1):
                                        path = f'../data/{year}/{funding_type_dict[funding_type]}/{subject2_dict[subject2]}/page{page}'
                                        os.makedirs(path, exist_ok=True)
                                        exist_files = show_files(path, [])
                                        if len(exist_files) >= 10:
                                            continue
                                        else:
                                            params['page'] = page
                                            child_resp = requests.get(url, headers=headers, params=params)
                                            time.sleep(0.5)
                                            child_resp.encoding = 'utf-8'
                                            child_tree = etree.HTML(child_resp.text)
                                            access_exception = child_tree.xpath('//h1//text()')
                                            if (child_resp.status_code == 200) & (access_exception[0] != '访问异常，请稍后再试~ '):
                                                # 提取项目卡片
                                                cards = child_tree.xpath('//div[@class="item-box layui-card "]')

                                                # 构建JSON数据
                                                for card in cards:
                                                    title = card.xpath('./a/@title')[0]
                                                    detail_href = card.xpath('./a/@href')[0]
                                                    project_num = \
                                                    card.xpath('.//div[contains(text(), "项目批准号：")]/text()')[0].split("：")[
                                                        1].strip()
                                                    approval_year = \
                                                    card.xpath('.//div[contains(text(), "批准年份：")]/text()')[0].split("：")[
                                                        1].strip()
                                                    discipline = \
                                                    card.xpath('.//div[contains(text(), "学科分类：")]/text()')[0].split("：")[
                                                        1].strip()
                                                    leader = \
                                                    card.xpath('.//div[contains(text(), "负责人：")]/text()')[0].split("：")[
                                                        1].strip()
                                                    province = \
                                                    card.xpath('.//div[contains(text(), "省份：")]/text()')[0].split("：")[
                                                        1].strip()
                                                    institution = \
                                                    card.xpath('.//div[contains(text(), "依托单位：")]/text()')[0].split("：")[
                                                        1].strip()
                                                    funding = \
                                                    card.xpath('.//div[contains(text(), "资助金额：")]/text()')[0].split("：")[
                                                        1].strip()
                                                    category = \
                                                    card.xpath('.//div[contains(text(), "资助类别：")]/text()')[0].split("：")[
                                                        1].strip()
                                                    keywords = \
                                                    card.xpath('.//div[contains(text(), "关键词：")]/text()')[0].split("：")[
                                                        1].strip()
                                                    outcomes = \
                                                    card.xpath('.//div[contains(text(), "研究成果：")]/text()')[0].split("：")[
                                                        1].strip()
                                                    participants = \
                                                    card.xpath('.//div[contains(text(), "参与人数:")]/text()')[0].split(":")[
                                                        1].strip()
                                                    file_path = os.path.join(path, f'{project_num}.json')
                                                    if os.path.isfile(file_path):
                                                        continue
                                                    else:
                                                        full_detail_href = urljoin(child_resp.url, detail_href)
                                                        detail_resp = requests.get(full_detail_href, headers=headers)
                                                        time.sleep(0.5)
                                                        detail_resp.encoding = 'utf-8'
                                                        detail_tree = etree.HTML(detail_resp.text)
                                                        access_exception = detail_tree.xpath('//h1//text()')
                                                        if (detail_resp.status_code == 200) & (access_exception[0] != '访问异常，请稍后再试~ '):
                                                            span_text = detail_tree.xpath(
                                                                '//div[label[contains(text(), "负责人职称：")]]/span/text()')
                                                            if (span_text is None) or (len(span_text) == 0):
                                                                academic_title = ''
                                                                with open('../data/error.txt', mode='a', encoding='utf-8_sig') as error_f:
                                                                    error_f.write(f'{url}\n')
                                                            else:
                                                                academic_title = span_text[0]
                                                            is_empty = detail_tree.xpath('//div[@id="canyu_wrapper"]//p[@class="empty-data"]/text()')
                                                            if (is_empty is None) or (len(is_empty) == 0):
                                                                # 提取表格数据
                                                                project_join_table = detail_tree.xpath('//div[@id="canyu_wrapper"]//table[@class="layui-table"]')[0]
                                                                table_headers = [header.text for header in
                                                                                 project_join_table.xpath('.//thead//th')]
                                                                table_rows = project_join_table.xpath('.//tbody//tr')
                                                                join_table = []
                                                                for row in table_rows:
                                                                    cells = row.xpath('.//td')
                                                                    table_item = {table_headers[i]: cells[i].text for i in
                                                                                  range(len(cells))}
                                                                    join_table.append(table_item)
                                                            else:
                                                                join_table = []
                                                        else:
                                                            with open('../data/error.txt', mode='a', encoding='utf-8_sig') as error_f:
                                                                error_f.write(f'{detail_resp.url}\n')
                                                            time.sleep(360)
                                                            join_table = []
                                                            academic_title = ''
                                                        item = {
                                                            "标题": title,
                                                            "项目批准号": project_num,
                                                            "批准年份": approval_year,
                                                            "学科分类": discipline,
                                                            "负责人": leader,
                                                            "负责人职称": academic_title,
                                                            "省份": province,
                                                            "依托单位": institution,
                                                            "资助金额": funding,
                                                            "资助类别": category,
                                                            "关键词": keywords,
                                                            "研究成果": outcomes,
                                                            "参与人数": participants,
                                                            "项目参与人": join_table
                                                        }
                                                        # 将JSON数据保存到文件
                                                        with open(file_path, 'a', encoding='utf-8') as f:
                                                            f.write(json.dumps(item, ensure_ascii=False, indent=4))
                                                        print(f'{item}\n-------------------------------------------------')
                                            else:
                                                with open('../data/error.txt', mode='a', encoding='utf-8_sig') as error_f:
                                                    error_f.write(f'{child_resp.url}\n')
                                            print(f'====={year}/{funding_type_dict[funding_type]}/{subject2_dict[subject2]}/{page}页完成=====')

                                else:
                                    with open('../data/search_overflow.txt', mode='a', encoding='utf-8_sig') as error_f:
                                        error_f.write(f'{url}\n')
                                    time.sleep(360)
                        else:
                            with open('../data/error.txt', mode='a', encoding='utf-8_sig') as error_f:
                                error_f.write(f'{url}\n')
                            time.sleep(360)
                        with open('../data/over.txt', mode='a', encoding='utf-8_sig') as over_f:
                            over_f.write(f'{url}\n')
                    except requests.exceptions.RequestException as err:
                        print("其他错误:", err)
                        time.sleep(360)
