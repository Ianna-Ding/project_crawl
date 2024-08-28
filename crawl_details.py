import time
import os
import requests
from lxml import etree
from urllib.parse import urljoin
import json
from fake_useragent import UserAgent
import re
import random
import csv


requests.packages.urllib3.disable_warnings()


stops_space = (
        ' '
        '\xa0'  # 空格:不间断空白符 &nbsp(non-breaking space)，
        '\u3000'  # 顶格 
        '\u2002'  # 空格
        '\u2003'  # 2空格
        '\u3000',
        '\n')  # '\|'


accounts = [
        {"mobile": "15921030319", "pwd": "shjtdxwyz2022"},
        {"mobile": "18556356687", "pwd": "hshwk123"},
        {"mobile": "15026550949", "pwd": "6666666666"},
        {"mobile": "13723015921", "pwd": "jzyb199707"},
        {"mobile": "13924177919", "pwd": "@Tian618"},
        {"mobile": "13052388865", "pwd": "nj8sj.fGpjMQ@m"},
        {"mobile": "18935897814", "pwd": "Saya030124"},
        {"mobile": "18811322359", "pwd": "2XTA5srk2@45VuA"},
        {"mobile": "19850075672", "pwd": "izaiwen72"},
        {"mobile": "18800269809", "pwd": "liji2014"}
    ]


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5000/delete/?proxy={}".format(proxy))


def get_proxy():
    while True:
        try:
            # 获取IP
            proxy_response = requests.get("http://127.0.0.1:5000/get/")
            proxy = proxy_response.json().get("proxy")

            if not proxy:
                print("未获取到IP，等待3秒后重试")
                time.sleep(3)
                continue

            # 测试IP是否支持HTTPS
            test_url = "https://httpbin.org/ip"
            headers = {
                'User-Agent': UserAgent().random
            }
            proxies = {"https": f"https://{proxy}"}
            response = requests.get(test_url, proxies=proxies, headers=headers, timeout=5)
            time.sleep(0.5)

            if response.status_code == 200:
                print(f"IP{proxy}通过HTTPS测试")
                return proxy
            else:
                print(f"IP{proxy}不支持HTTPS，等待0.5秒后重试")
                time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"IP{proxy}不可用: {e}")
            if proxy:
                delete_proxy(proxy)  # 删除无效的IP
            print("等待0.5秒后重试")
            time.sleep(0.5)


class SessionManager:
    def __init__(self, accounts):
        self.accounts = accounts
        self.current_index = 0
        self.session = None
        self.max_attempts = 3  # 每个账号在同一个IP上的最大重试次数
        self.ip_switch_limit = 5  # 更换5个IP后切换账号
        self.attempt_count = 0
        self.ip_switch_count = 0

    def get_current_account(self):
        return self.accounts[self.current_index]

    def create_new_session(self):
        # 重置尝试次数和IP切换计数
        self.attempt_count = 0
        self.ip_switch_count = 0
        account = self.get_current_account()
        mobile, pwd = account['mobile'], account['pwd']
        print(f"使用账号{mobile}尝试登录")
        self.session, self.current_proxy = self.login_with_retry(mobile, pwd)
        if self.session:
            print(f"账号{mobile}登录成功，使用IP{self.current_proxy}")
        else:
            print(f"账号{mobile}登录失败，切换账号")
            self.switch_to_next_account()

    def login_with_retry(self, mobile, pwd):
        for _ in range(self.ip_switch_limit):
            proxy = get_proxy()
            session = self.login(mobile, pwd, proxy)
            if session:
                return session, proxy
            else:
                print(f"更换IP{proxy}")
        return None, None

    def login(self, mobile, pwd, proxy):
        login_url = f"https://www.izaiwen.cn/user/mobileLogin?mobile={mobile}&pwd={pwd}"
        session = requests.Session()
        headers = {
            'Connection': 'keep-alive',
            'User-Agent': UserAgent().random
        }
        try:
            response = session.get(login_url, proxies={"https": f"https://{proxy}"}, headers=headers, verify=False, timeout=(10, 10))
            if response.status_code == 200:
                verified_response = session.get('https://www.izaiwen.cn/ajax/user/signinrecord', proxies={"https": f"https://{proxy}"}, headers=headers, verify=False, timeout=(10, 10))
                if verified_response.status_code == 200 and verified_response.json().get("code") == 0:
                    print("登录成功")
                    session.cookies.update(verified_response.cookies)
                    session.headers.update(headers)
                    return session
        except Exception as e:
            print(f"登录失败: {e}")
        return None

    def switch_to_next_account(self):
        self.current_index += 1
        if self.current_index >= len(self.accounts):
            self.current_index = 0
            print("所有账号都失败，等待1分钟后重试")
            time.sleep(60)
        self.create_new_session()

    def get_session(self):
        if self.session is None:
            self.create_new_session()
        return self.session

    def increment_attempt(self):
        self.attempt_count += 1
        if self.attempt_count >= self.max_attempts:
            print(f"账号{self.accounts[self.current_index]['mobile']}在IP{self.current_proxy}上达到最大尝试次数，切换IP")
            self.ip_switch_count += 1
            if self.ip_switch_count >= self.ip_switch_limit:
                print(f"账号{self.accounts[self.current_index]['mobile']}更换了{self.ip_switch_limit}次IP后仍然失败，切换账号")
                self.switch_to_next_account()
            else:
                # 更换IP并重置尝试次数
                self.session, self.current_proxy = self.login_with_retry(self.accounts[self.current_index]['mobile'], self.accounts[self.current_index]['pwd'])
                self.attempt_count = 0


def remove_stops_space(input_string):
    # 创建转换表，将这些字符映射到 None
    translation_table = str.maketrans('', '', ''.join(stops_space))
    return input_string.translate(translation_table)


def proxy_geturl(session_manager, url, referer):
    while True:
        try:
            session = session_manager.get_session()
            headers = {
                'Connection': 'keep-alive',
                'User-Agent': UserAgent().random,
                'Referer': referer
            }

            # 使用当前session和IP发起请求
            proxy = session_manager.current_proxy
            proxies = {"https": f"https://{proxy}"}

            rsp = session.get(url, headers=headers, proxies=proxies, verify=False, timeout=(10, 10))
            rsp.encoding = 'utf-8'
            session.cookies.update(rsp.cookies)
            session.headers.update(headers)

            # 检查网页内容
            if "访问异常" in rsp.text:
                print("检测到'访问异常'，立即更换账号和IP")
                session_manager.switch_to_next_account()
                continue

            if "再问科研" not in rsp.text:
                print("未找到'再问科研'，优先更换IP")
                session_manager.increment_attempt()
                continue

            # 如果请求成功且内容符合预期
            print("请求成功")
            return rsp.text

        except Exception as e:
            print(f"请求失败: {e}")
            session_manager.increment_attempt()
            time.sleep(random.randint(1, 9) * 0.2)


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
        all_folders = [os.path.join(parent_dir, name) for name in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, name))]

        # 找到最新的文件夹
        latest_subfolder = os.path.basename(max(all_folders, key=os.path.getmtime))

        # 获取当前文件夹的名称
        current_folder = os.path.basename(path)

        # 检查当前文件夹是否是最后一个文件夹
        return latest_subfolder == current_folder
    else:
        return False


def fetch_details_data(child_url, detail_href, session_manager):
    full_detail_href = urljoin(child_url, detail_href)
    detail_resp = proxy_geturl(session_manager, full_detail_href, child_url)
    time.sleep(0.5)
    detail_tree = etree.HTML(detail_resp)
    if detail_resp != '':
        span_text = detail_tree.xpath(
            '//div[label[contains(text(), "负责人职称：")]]/span/text()')
        if (span_text is None) or (len(span_text) == 0):
            academic_title = ''
        else:
            academic_title = span_text[0]
        is_empty = detail_tree.xpath('//div[@id="canyu_wrapper"]//p[@class="empty-data"]/text()')
        if (is_empty is None) or (len(is_empty) == 0):
            # 提取表格数据
            project_join_table = \
                detail_tree.xpath('//div[@id="canyu_wrapper"]//table[@class="layui-table"]')[0]
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
        is_empty_fruit = detail_tree.xpath('//div[@id="fruit_wrapper"]//p[@class="empty-data"]/text()')
        if (is_empty_fruit is None) or (len(is_empty_fruit) == 0):
            # 提取表格数据
            fruit_table = detail_tree.xpath('//div[@id="fruit_wrapper"]//table[@class="layui-table"]')[0]
            fruit_table_headers = [header.text for header in
                             fruit_table.xpath('.//thead//th')]
            fruit_table_rows = fruit_table.xpath('.//tbody//tr')
            fruit_join_table = []
            for fruit_row in fruit_table_rows:
                fruit_cells = fruit_row.xpath('.//td')
                fruit_table_item = {}
                for fruit_num in range(len(fruit_cells)):
                    if fruit_table_headers[fruit_num] == '标题':
                        fruit_table_item[fruit_table_headers[fruit_num]] = ''.join(fruit_cells[fruit_num].xpath('./a/@title'))
                    else:
                        fruit_table_item[fruit_table_headers[fruit_num]] = fruit_cells[fruit_num].text
                fruit_join_table.append(fruit_table_item)
        else:
            fruit_join_table = []
        return academic_title, join_table, fruit_join_table
    else:
        print(f'Failed to fetch data: {full_detail_href}')
        time.sleep(240)
        fetch_details_data(child_url, detail_href, session_manager)


def fetch_page_data(year, funding_type, subject2, child_url, path, session_manager, url):
    try:
        child_resp = proxy_geturl(session_manager, child_url, url)
        time.sleep(0.5)
        if child_resp != '':
            child_tree = etree.HTML(child_resp)
            project_num_lst = child_tree.xpath(
                '//div[@class="item-box layui-card "]//div[contains(text(), "项目批准号：")]/text()')
            project_num_lst = [x.strip() for x in project_num_lst]
            with open(os.path.join(path, 'project_num_lst.json'), mode='w', encoding='utf-8') as lf:
                lf.write(json.dumps(project_num_lst, ensure_ascii=False, indent=4))
            # 提取项目
            cards = child_tree.xpath('//div[@class="item-box layui-card "]')

            # 构建JSON
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
                    academic_title, join_table, fruit_join_table = fetch_details_data(child_url, detail_href, session_manager)
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
                        "研究成果表": fruit_join_table,
                        "参与人数": participants,
                        "项目参与人": join_table
                    }

                    with open(file_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(item, ensure_ascii=False, indent=4))
                    print(f'{item}\n-------------------------------------------------')
        else:
            print(f'Failed to fetch data: {child_url}')
            time.sleep(240)
            fetch_page_data(year, funding_type, subject2, child_url, path, session_manager, url)
    except:
        print(f'Failed to fetch data: {child_url}')
        time.sleep(240)
        fetch_page_data(year, funding_type, subject2, child_url, path, session_manager, url)


def fetch_url_data(year, funding_type, subject2, session_manager):
    url = f"https://www.izaiwen.cn/pro/{funding_type}-{subject2}?psnname=&orgname=&prjno=&sy={year}&ey={year}&sjy=&ejy=&st=&et=&keyword=&canyu_name=&canyu_orgname="
    referer = f"https://www.izaiwen.cn/pro/{funding_type}-{subject2}"
    try:
        resp = proxy_geturl(session_manager, url, referer)
        time.sleep(0.5)
        if resp != '':
            tree = etree.HTML(resp)
            # 提取查询总数
            results_num = tree.xpath('//blockquote[@class="m-t-34 m-b-25 total-result"]//span[@class="num"]/text()')
            if (results_num is None) or (len(results_num) == 0):
                with open('../data/error.txt', mode='a', encoding='utf-8_sig') as error_f:
                    error_f.write(f'{url}\n')
                time.sleep(360)
            else:
                results_num_real = int(results_num[0].strip())
                if results_num_real <= 5000:
                    if results_num_real <= 10:
                        final_page = 1
                    else:
                        page_num = tree.xpath('//li[@class="page-item"]/a/text()')
                        final_page = int(page_num[-2])
                    with open('../data/page_result_num.csv', mode='a', encoding='utf-8_sig', newline='') as page_f:
                        writer = csv.writer(page_f)
                        writer.writerow([year, funding_type, subject2, final_page, results_num_real])
                    for page in range(1, final_page + 1):
                        path = f'../data/{year}/{funding_type_dict[funding_type]}/{subject2_dict[subject2]}/page{page}'
                        os.makedirs(path, exist_ok=True)
                        exist_files = show_files(path, [])
                        if len(exist_files) >= 11:
                            continue
                        else:
                            child_url = f"https://www.izaiwen.cn/pro/{funding_type}-{subject2}?sy={year}&ey={year}&page={page}"
                            if page == 1:
                                fetch_page_data(year, funding_type, subject2, child_url, path, session_manager, url)
                            else:
                                fetch_page_data(year, funding_type, subject2, child_url, path, session_manager, f"https://www.izaiwen.cn/pro/{funding_type}-{subject2}?sy={year}&ey={year}&page={page-1}")
                            print(
                                f'====={year}/{funding_type_dict[funding_type]}/{subject2_dict[subject2]}/{page}页完成=====')

                else:
                    with open('../data/search_overflow.txt', mode='a', encoding='utf-8_sig') as error_f:
                        error_f.write(f'{url}\n')
                    time.sleep(240)
        else:
            with open('../data/error.txt', mode='a', encoding='utf-8_sig') as error_f:
                error_f.write(f'{url}\n')
            time.sleep(240)
            fetch_url_data(year, funding_type, subject2, session_manager)
        with open('../data/over.txt', mode='a', encoding='utf-8_sig') as over_f:
            over_f.write(f'{url}\n')
    except:
        print(f'Failed to fetch data: {url}')
        with open('../data/error.txt', mode='a', encoding='utf-8_sig') as error_f:
            error_f.write(f'{url}\n')
        time.sleep(240)
        fetch_url_data(year, funding_type, subject2, session_manager)



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
        if item.strip() != 'sonQT-stwQT|QT.其它':
            lst = item.strip().split('|')
            subject2_dict[lst[0]] = lst[1]

    session_manager = SessionManager(accounts)
    for year in range(2019, 2024):
        for funding_type in funding_type_dict:
            for subject2 in subject2_dict:
                folder_path = f'../data/{year}/{funding_type_dict[funding_type]}/{subject2_dict[subject2]}'
                if (os.path.isdir(folder_path) == False) or (is_last_folder_in_directory(folder_path) == True):
                    os.makedirs(folder_path, exist_ok=True)
                    fetch_url_data(year, funding_type, subject2, session_manager)

