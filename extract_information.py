import os
import json

import pandas as pd
from tqdm import tqdm
import csv
import re
import html
from lxml import etree

import matplotlib.pyplot as plt


def show_files(path, all_files):
    file_list = os.listdir(path)
    for f in file_list:
        cur_path = os.path.join(path, f)
        if os.path.isdir(cur_path):
            show_files(cur_path, all_files)
        else:
            all_files.append(cur_path)
    return all_files


def fetch_page_data(url_path):
    with open(url_path, 'r', encoding='utf-8') as file:
        rsp = file.read()
    cleaned_html = re.sub(r'<td\b[^>]*>(.*?)</td>', r'\1', rsp)
    cleaned_html = re.sub(r'<tr\b[^>]*>(.*?)</tr>', r'\1', cleaned_html)
    cleaned_html = re.sub(r'<span\b[^>]*>(.*?)</span>', r'\1', cleaned_html)
    cleaned_html = re.sub(r'<span\b[^>]*>(.*?)</span>', r'\1', cleaned_html)
    cleaned_html = re.sub(r'<a class="html-attribute-value[^>]*>(.*?)</a>', r'\1', cleaned_html)

    cleaned_html = html.unescape(cleaned_html)
    child_tree = etree.HTML(cleaned_html)
    cards = child_tree.xpath('//div[@class="item-box layui-card "]')
    for card in cards:
        title = card.xpath('./a/@title')[0]
        if title == '':
            if len(card.xpath('.//span[@class="tit-name"]/text()'))>0:
                title = card.xpath('.//span[@class="tit-name"]/text()')[0].strip()
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
        item = {
            "标题": title,
            "项目批准号": project_num,
            "批准年份": approval_year,
            "学科分类": discipline,
            "负责人": leader,
            "省份": province,
            "依托单位": institution,
            "资助金额": funding,
            "资助类别": category,
            "关键词": keywords,
            "研究成果": outcomes,
            "参与人数": participants
        }

        with open('../data/project.csv', mode='a', encoding='utf-8_sig', newline='') as page_f:
            writer = csv.writer(page_f)
            writer.writerow([title, project_num, approval_year, discipline, leader, province, institution,
                             funding, category, keywords, outcomes, participants, url_path])
        print(f'{item}\n-------------------------------------------------')


if __name__ == '__main__':
    html_lst = show_files('../data2/data', [])
    with open('../data/project.csv', mode='a', encoding='utf-8_sig', newline='') as page_f:
        writer = csv.writer(page_f)
        writer.writerow(["标题", "项目批准号", "批准年份", "学科分类", "负责人", "省份", "依托单位",
                         "资助金额", "资助类别", "关键词", "研究成果", "参与人数", "来源"])
    for i in tqdm(html_lst, desc='extract', total=len(html_lst)):
        fetch_page_data(i)

    project = pd.read_csv('../data/project.csv')
    project.isnull().sum()
    project[project['项目批准号'].isnull()][["项目批准号", "批准年份", "学科分类", "资助类别", "来源"]]
    project[project['依托单位'].isnull()][["项目批准号", "批准年份", "学科分类", "资助类别"]]

    project.drop_duplicates(inplace=True)
    project.to_csv('../data/project.csv', index=False, encoding='utf-8_sig')
    project["项目批准号"] = project["项目批准号"].astype(str)

    project_keys = project.columns.to_list()
    json_lst = show_files('../data', [])
    for json_file in tqdm(json_lst, desc='extract', total=len(json_lst)):
        if json_file.endswith('.json'):
            json_num = os.path.basename(json_file).replace('.json', '')
            if (json_num != 'project_num_lst') and (json_num not in project["项目批准号"]):
                with open(json_file, mode='r', encoding='utf-8') as f:
                    json_dict = json.load(f)
                row = []
                for k in project_keys:
                    if k != "来源":
                        row.append(json_dict[k])
                    else:
                        row.append(json_file)
                with open('../data/project.csv', mode='a', encoding='utf-8_sig', newline='') as page_f:
                    writer = csv.writer(page_f)
                    writer.writerow(row)

    project = pd.read_csv('../data/project.csv')
    project.isnull().sum()
    project[project['项目批准号'].isnull()][["项目批准号", "批准年份", "学科分类", "资助类别", "来源"]]
    for i in project[project['项目批准号'].isnull()]['来源']:
        with open(i, mode='r', encoding='utf-8') as f:
            json_dict = json.load(f)
        title = json_dict['标题']
        if len(project[project['标题'] == title].copy()) == 0:
            print(title, '来源')

    for i in project[project['项目批准号'].isnull()]['来源']:
        with open(i, mode='r', encoding='utf-8') as f:
            json_dict = json.load(f)
        project = project[project['来源'] != i].copy()

    # project[project['项目批准号'].duplicated()]["来源"]
    # project[project['项目批准号'] == '11922103'][["来源"]]
    project.drop_duplicates(subset=["标题", "项目批准号", "批准年份", "学科分类", "负责人", "省份", "依托单位", "资助金额", "资助类别", "关键词", "研究成果", "参与人数"], inplace=True)
    project.to_csv('../data/project20241023.csv', index=False, encoding='utf-8_sig')
    project.drop(columns="来源", inplace=True)
    project.to_csv('../data/project_izaiwen.csv', index=False, encoding='utf-8_sig')

    # draw
    project_group = project.groupby(['批准年份', '资助类别']).size().unstack(fill_value=0)
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    # stack bar
    colormap = plt.get_cmap('tab20')
    ax = project_group.plot(kind='bar', stacked=True, figsize=(12, 8), colormap=colormap)
    plt.title('每年各个资助类别的项目数量对比')
    plt.xlabel('批准年份')
    plt.ylabel('项目数量')
    plt.legend(title='资助类别', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('../data/project_funding_comparison_stack.png', bbox_inches='tight')
    plt.show()

    # bar
    fig, axes = plt.subplots(nrows=1, ncols=5, figsize=(20, 6), sharey=True)
    for i, year in enumerate(range(2019, 2024)):
        ax = axes[i]
        project_group.loc[f'{year}年'].plot(kind='barh', ax=ax, title=f'{year}年')
        for index, value in enumerate(project_group.loc[f'{year}年']):
            ax.text(value, index, str(value), va='center')
        ax.set_xlabel('项目数量')

    # 只在第一个子图上设置y轴标签为“资助类别”
    axes[0].set_ylabel('资助类别')
    plt.tight_layout()
    fixed_file_path = '../data/project_funding_comparison.png'
    plt.savefig(fixed_file_path)
    plt.show()