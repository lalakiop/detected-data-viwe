import os
import re
import json
from datetime import datetime

# 定义需要提取的元素
elements = ['Si', 'Cu', 'Mg', 'Fe', 'Zn', 'Ni', 'Mn', 'Ti', 'Sn', 'Pb', 'Cr', 'Al']

# 计算污泥指数，保留三位小数
def calculate_sludge_index(fe, mn, cr):
    sludge_index = 1 * fe + 2 * mn + 3 * cr
    return round(sludge_index, 3)  # 保留三位小数

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

#预处理
def clean_text(content):
    return re.sub(r'[-+<]', '', content)
    
    
# 主函数，遍历文件夹并处理每个文件
def process_folder(folder_path, data_file):
    #print(folder_path)
    result = load_processed_data(data_file)  # 加载已处理的数据

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        #print(filename)
        if filename.lower().endswith(".txt"):  # 假设文件是txt格式
            file_path = os.path.join(folder_path, filename)
            #print(file_path)

            # 提取炉号和检测次数
            furnace_number, test_number = parse_filename(filename)
            #print(furnace_number)
            #print(test_number)

            # 检查该炉号和检测次数是否已经处理过
            if furnace_number in result and test_number in result[furnace_number]:
                #print(f"文件 {filename} 已经处理过，跳过")
                continue  # 如果已处理过，跳过

            # 读取文件内容
            content = read_file_content(file_path)
            #去掉 - + <
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
                    "time": file_time
                }

            # 获取并排序测试编号
            sorted_test_number = sorted(
                [key for key in result[furnace_number].keys() if key.startswith('Q')] +  # 先选出所有Q开头的键
                [key for key in result[furnace_number].keys() if key.isdigit()],  # 然后是所有数字键
                key=lambda x: (x.startswith('Q'), x)  # 排序规则：Q系列优先，其他按自然顺序排序
            )

            # 按排序顺序重新排列字典
            result[furnace_number] = {key: result[furnace_number][key] for key in sorted_test_number}

            #print(f"处理了文件 {filename}")
    
    # 保存更新后的数据到JSON文件
    save_data_to_json(result, data_file)

# 使用示例
folder_path = r"\\192.168.101.150\\cp"  # 请替换为实际文件夹路径
output_file = "data.json"  # 结果将保存到这个文件

# 处理文件夹中的所有文件并保存结果
process_folder(folder_path, output_file)

#print(f"数据已保存到 {output_file}")
