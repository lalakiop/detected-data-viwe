import json
import os
import re
from datetime import datetime

# 定义需要提取的元素
elements = ['Si', 'Cu', 'Mg', 'Fe', 'Zn', 'Ni', 'Mn', 'Ti', 'Sn', 'Pb', 'Cr', 'Al']

# 计算污泥指数，保留三位小数
def calculate_sludge_index(fe, mn, cr):
    sludge_index = 1 * fe + 2 * mn + 3 * cr
    return round(sludge_index, 3)

# 提取文件内容中的元素含量
def extract_elements_from_content(content):
    element_data = {}
    # 正则表达式用于提取元素及其含量
    for element in elements:
        match = re.search(rf"{element}\s+([<\d.]+)", content)
        if match:
            value = match.group(1)
            if value == "<":
                element_data[element] = 0.0  # 小于某个值时设为0
            else:
                element_data[element] = round(float(value), 3)
    return element_data

# 提取文件名中的炉号和检测次数
def parse_filename(filename):
    parts = re.split(r"[-.]", filename)
    furnace_number = parts[0]
    test_number = parts[1]
    return furnace_number, test_number

# 读取文件内容
def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# 获取文件的保存时间
def get_file_creation_time(file_path):
    timestamp = os.path.getmtime(file_path)
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# 读取已处理的炉号和检测次数数据
def load_processed_data(data_file):
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 保存结果到JSON文件
def save_data_to_json(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

# 预处理
def clean_text(content):
    """去除特殊字符和指定的关键词（不区分大小写）"""
    # 去掉 "-", "+", "<"
    content = re.sub(r'[-+<]', '', content)

    # 去掉 "ADC12Z" 和 "AlSi10MnMg"（忽略大小写）
    content = re.sub(r'(?i)ADC12Z|AlSi10MnMg', '', content)

    return content

# 检测牌号
def test_brand(content):
    """检测文本中是否包含指定的品牌名称，不区分大小写，返回第一个匹配的品牌"""
    # 品牌列表（可扩展）
    brands = ["ALSi10MnMg", "ADC12Z", "ADC12", "A380"]

    # 构造正则表达式，使用 `|` 连接多个品牌名称，并启用 `re.IGNORECASE`
    pattern = re.compile(r'\b(' + '|'.join(brands) + r')\b', re.IGNORECASE)

    # 搜索匹配项
    match = pattern.search(content)

    # 如果找到匹配项，返回匹配的品牌，否则返回 None
    return match.group(1) if match else None

# 读取txt主函数，遍历文件夹并处理每个文件
def process_folder(folder_path, data_file):
    result = load_processed_data(data_file)  # 加载已处理的数据

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".txt"):  # 假设文件是txt格式
            file_path = os.path.join(folder_path, filename)

            # 提取炉号和检测次数
            furnace_number, test_number = parse_filename(filename)

            # 检查该炉号和检测次数是否已经处理过
            if furnace_number in result and test_number in result[furnace_number]:
                continue  # 如果已处理过，跳过

            # 读取文件内容
            content = read_file_content(file_path)
            a_brand = test_brand(content)
            # 去掉 - + <
            content = clean_text(content)

            # 提取元素数据
            element_data = extract_elements_from_content(content)

            # 计算污泥指数
            sludge_index = calculate_sludge_index(
                element_data.get('Fe', 0.0),
                element_data.get('Mn', 0.0),
                element_data.get('Cr', 0.0)
            )

            # 获取文件保存时间
            file_time = get_file_creation_time(file_path)

            # 生成数据结构
            if furnace_number not in result:
                result[furnace_number] = {}

            # 添加测试编号到炉号字典中（确保存在）
            if test_number not in result[furnace_number]:
                result[furnace_number][test_number] = {
                    **element_data,
                    "污泥指数": sludge_index,
                    "time": file_time,
                    "牌号": a_brand
                }

            # 获取并排序测试编号
            sorted_test_number = sorted(
                [key for key in result[furnace_number].keys() if key.startswith('Q')] +  # 先选出所有Q开头的键
                [key for key in result[furnace_number].keys() if key.isdigit()],  # 然后是所有数字键
                key=lambda x: (x.startswith('Q'), x)  # 排序规则：Q系列优先，其他按自然顺序排序
            )

            # 按排序顺序重新排列字典
            result[furnace_number] = {key: result[furnace_number][key] for key in sorted_test_number}

    # 保存更新后的数据到JSON文件
    save_data_to_json(result, data_file)

def sotrjson():
    # 输入文件和输出文件路径
    input_file = "data.json"  # 确保 data.json 在脚本所在目录
    output_files = {
        "1": "data1.json",
        "2": "data2.json",
        "3": "data3.json",
    }

    # 读取 JSON 文件
    if not os.path.exists(input_file):
        return

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 存储分类后的数据
    sorted_data = {"1": {}, "2": {}, "3": {}}

    # 解析数据并分类
    for furnace_id, records in data.items():
        group_id = furnace_id[0]  # 获取炉组号的第一位数字
        if group_id in sorted_data:
            sorted_data[group_id][furnace_id] = records

    # 处理每个炉组的数据
    for group_id, records in sorted_data.items():
        # 只保留最新的 5 个炉次号
        latest_furnaces = sorted(records.keys(), key=int, reverse=True)[:5]

        # 生成最终数据
        filtered_data = {furnace: records[furnace] for furnace in latest_furnaces}

        # 获取目标文件路径
        output_file = output_files[group_id]

        # 清空文件（覆盖写入），确保不会保留旧数据
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({}, f)

        # 写入最新数据
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(filtered_data, f, indent=4, ensure_ascii=False)

def load_json_data(filename):
    """加载 JSON 数据"""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def sort_furnace_tests(test_ids):
    """按照规则排序炉次号"""
    q_tests = sorted([tid for tid in test_ids if re.match(r"^[Qq]\d+$", tid)], key=lambda x: int(x[1:]))
    num_tests = sorted([tid for tid in test_ids if tid.isdigit()], key=int)
    return q_tests + num_tests