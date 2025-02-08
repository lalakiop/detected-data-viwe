import json
import os

# 输入文件和输出文件路径
input_file = "data.json"  # 确保 data.json 在脚本所在目录
output_files = {
    "1": "data1.json",
    "2": "data2.json",
    "3": "data3.json",
}

# 读取 JSON 文件
if not os.path.exists(input_file):
    #print(f"错误：{input_file} 文件不存在！")
    exit()

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

    # **清空文件（覆盖写入），确保不会保留旧数据**
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({}, f)

    # **写入最新数据**
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, indent=4, ensure_ascii=False)

#print("数据分类完成，文件已更新！")
