import tkinter as tk
from tkinter import ttk
import json
import os
import re
import threading
import time
import subprocess 
from datetime import datetime 

# 目标 JSON 文件路径
json_files = ["data1.json", "data2.json", "data3.json"]
refresh_interval = 60  # 自动刷新间隔（秒）
countdown = refresh_interval  # 倒计时初始值
#########################################################
#读取txt
#########################################################
# 定义需要提取的元素
elements = ['Si', 'Cu', 'Mg', 'Fe', 'Zn', 'Ni', 'Mn', 'Ti', 'Sn', 'Pb', 'Cr', 'Al']
# 使用示例
txtfolder_path = r"\\192.168.101.150\\cp"  # 请替换为实际文件夹路径
dataoutput_file = "data.json"  # 结果将保存到这个文件
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
    """去除特殊字符和指定的关键词（不区分大小写）"""
    # 去掉 "-", "+", "<"
    content = re.sub(r'[-+<]', '', content)

    # 去掉 "ADC12Z" 和 "AlSi10MnMg"（忽略大小写）
    content = re.sub(r'(?i)ADC12Z|AlSi10MnMg', '', content)

    return content

#检测牌号

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
            a_brand = test_brand(content)
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

            #print(f"处理了文件 {filename}")
    
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

def update_treeview(treeview, data, furnace_id):
    """更新 Treeview 数据"""
    treeview.delete(*treeview.get_children())
    if furnace_id in data:
        sorted_tests = sort_furnace_tests(data[furnace_id].keys())
        for test_num in sorted_tests:
            values = data[furnace_id][test_num]
            treeview.insert("", "end", values=[furnace_id, test_num] + list(values.values()))

def on_combobox_change(event, treeview, data):
    """当用户选择炉次号时更新表格"""
    selected_furnace = event.widget.get()
    update_treeview(treeview, data, selected_furnace)

def refresh_data(treeviews, comboboxes, brand_labels, countdown_label):
    """手动刷新数据并重置倒计时"""
    global countdown
    countdown = refresh_interval
    update_countdown(countdown_label)

    for i, json_file in enumerate(json_files):
        data = load_json_data(json_file)
        combobox = comboboxes[i]
        brand_label = brand_labels[i]  # 获取对应炉号的品牌标签

        furnace_ids = sorted(data.keys(), key=int, reverse=True) if data else []
        default_furnace = furnace_ids[0] if furnace_ids else ""

        combobox["values"] = furnace_ids
        combobox.set(default_furnace)

        update_treeview(treeviews[i], data, default_furnace)

        # **更新牌号**
        if default_furnace in data:
            latest_test = max(data[default_furnace].keys(), key=str)
            brand = data[default_furnace][latest_test].get("牌号", "未知")
            brand_label.config(text=f"牌号：{brand}")


def auto_refresh(root, treeviews, comboboxes, brand_labels, countdown_label):
    """自动刷新逻辑"""
    global countdown
    if countdown > 0:
        countdown -= 1
        update_countdown(countdown_label)
    else:
        refresh_data(treeviews, comboboxes, brand_labels, countdown_label)  # 确保 `refresh_data` 也接收相应参数

    # 继续执行倒计时
    root.after(1000, lambda: auto_refresh(root, treeviews, comboboxes, brand_labels, countdown_label))


def copy_selected_rows(treeview):
    """复制选中的表格数据"""
    selected_items = treeview.selection()  # 获取选中的行
    if not selected_items:
        return

    # 需要复制的元素列（第 3-13 列 + 第 14 列）
    selected_columns = ["Si", "Cu", "Mg", "Fe", "Zn", "Ni", "Mn", "Ti", "Sn", "Pb", "Al"]

    # 获取表格的列索引
    column_ids = treeview["columns"]
    column_indexes = [column_ids.index(col) for col in selected_columns if col in column_ids]

    copied_data = []
    for item in selected_items:
        row_values = treeview.item(item, "values")
        copied_values = [row_values[i] for i in column_indexes]  # 直接取对应索引列的数据
        copied_data.append("\t".join(copied_values))  # `Tab` 作为 Excel 兼容的分隔符

    # 组合成最终的复制文本，使用 `\n` 换行
    clipboard_text = "\n".join(copied_data)
    root.clipboard_clear()
    root.clipboard_append(clipboard_text)
    root.update()  # 更新剪贴板
    print("✅ 数据已复制到剪贴板！")
    
def copy_selected_rows_alsi10(treeview):
    """复制选中的表格数据"""
    selected_items = treeview.selection()  # 获取选中的行
    if not selected_items:
        return

    # 需要复制的元素列（Si ~ Sn + Al）
    selected_columns = ["Si", "Cu", "Mg", "Fe", "Zn", "Ni", "Mn", "Ti", "Sn", "Al"]

    # 获取表格的列索引
    column_ids = treeview["columns"]
    column_indexes = [column_ids.index(col) for col in selected_columns if col in column_ids]

    copied_data = []
    for item in selected_items:
        row_values = treeview.item(item, "values")

        # 提取数值（转换为 float）
        extracted_values = [float(row_values[i]) for i in column_indexes]

        # 计算 100 - (Si + Cu + Mg + Fe + Zn + Ni + Mn + Ti + Sn + Al)，保留 4 位小数
        calculated_value = round(100 - sum(extracted_values), 4)

        # 组装数据，计算值插入 `Al` 之前
        copied_values = extracted_values[:-1] + [calculated_value, extracted_values[-1]]

        # 转换为字符串并拼接
        copied_data.append("\t".join(map(str, copied_values)))

    # 组合成最终的复制文本，使用 `\n` 换行
    clipboard_text = "\n".join(copied_data)
    root.clipboard_clear()
    root.clipboard_append(clipboard_text)
    root.update()  # 更新剪贴板
    print("✅ 数据已复制到剪贴板！")


def show_context_menu(event, treeview):
    """右键弹出菜单"""
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="ADC12Z", command=lambda: copy_selected_rows(treeview))
    context_menu.add_command(label="ALSI10", command=lambda: copy_selected_rows_alsi10(treeview))
    context_menu.post(event.x_root, event.y_root)


def update_countdown(label):
    """更新倒计时文本"""
    label.config(text=f"刷新倒计时: {countdown}s")



def run_external_scripts():
    """每 60 秒运行 readtxt.py，等待 3 秒后运行 sortjson.py"""
    while True:
        try:
            print("运行 读取txt文件")
            # 处理文件夹中的所有文件并保存结果
            process_folder(txtfolder_path, dataoutput_file)  # 运行 readtxt.py

            print("等待 3 秒...")
            time.sleep(3)

            print("运行整理json文件")
             # 运行 sortjson.py
            sotrjson()
            print(f"等待 {refresh_interval} 秒后重新运行...")
            time.sleep(refresh_interval)  # 等待 60 秒，进入下一次循环
        except Exception as e:
            print(f"运行外部脚本出错: {e}")

def on_mouse_drag_select(event, treeview):
    """鼠标拖动框选多行"""
    item = treeview.identify_row(event.y)  # 获取鼠标所在行
    if item:
        treeview.selection_add(item)  # 添加到选中列表

def on_combobox_change(event, treeview, data, brand_label):
    """当用户选择炉次号时，更新表格和牌号显示"""
    selected_furnace = event.widget.get()
    update_treeview(treeview, data, selected_furnace)

    # 获取最新的牌号信息（取最大次数的牌号）
    if selected_furnace in data:
        latest_test = max(data[selected_furnace].keys(), key=str)  # 选择最新的检测次数
        brand = data[selected_furnace][latest_test].get("牌号", "未知")
        brand_label.config(text=f"牌号：{brand}")  # 更新牌号显示


def create_gui():
    global root  # 需要全局 root 变量，供 `copy_selected_rows` 访问
    root = tk.Tk()
    root.title("炉号检测数据")

    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    treeviews = []
    comboboxes = []
    brand_labels = []  # 存储牌号标签

    # 刷新按钮 + 倒计时
    refresh_frame = tk.Frame(root)
    refresh_frame.pack(pady=5)

    refresh_button = tk.Button(refresh_frame, text="刷新", font=("Arial", 10),
                               command=lambda: refresh_data(treeviews, comboboxes, brand_labels, countdown_label))
    refresh_button.pack(side="left", padx=10)

    countdown_label = tk.Label(refresh_frame, text=f"刷新倒计时: {refresh_interval}s", font=("Arial", 10))
    countdown_label.pack(side="left")

    for i, json_file in enumerate(json_files):
        data = load_json_data(json_file)

        furnace_ids = sorted(data.keys(), key=int, reverse=True) if data else []
        default_furnace = furnace_ids[0] if furnace_ids else ""

        sub_frame = tk.Frame(frame)
        sub_frame.pack(fill="x", pady=5)

        top_frame = tk.Frame(sub_frame)
        top_frame.pack(fill="x")

        label = tk.Label(top_frame, text=f"{i+1}#炉", font=("Arial", 10, "bold"))
        label.pack(side="left", padx=5)

        combobox = ttk.Combobox(top_frame, values=furnace_ids, state="readonly")
        combobox.pack(side="left", padx=10)
        combobox.set(default_furnace)
        comboboxes.append(combobox)

        # **新增：牌号显示 Label**
        brand_label = tk.Label(top_frame, text="牌号：未知", font=("Arial", 10, "bold"))
        brand_label.pack(side="left", padx=5)
        brand_labels.append(brand_label)

        treeview = ttk.Treeview(sub_frame, columns=(
            "炉号", "次数", "Si", "Cu", "Mg", "Fe", "Zn", "Ni", "Mn", "Ti", "Sn", "Pb", "Cr", "Al", "污泥指数", "时间"),
            show="headings", selectmode="extended")  # **支持鼠标框选多行**

        columns = ["炉号", "次数", "Si", "Cu", "Mg", "Fe", "Zn", "Ni", "Mn", "Ti", "Sn", "Pb", "Cr", "Al", "污泥指数", "时间"]
        for col in columns:
            treeview.heading(col, text=col)
            treeview.column(col, width=80 if col == "炉号" else (160 if col == "时间" else 60))

        scrollbar = ttk.Scrollbar(sub_frame, orient="horizontal", command=treeview.xview)
        treeview.config(xscrollcommand=scrollbar.set)

        treeview.pack(fill="x", expand=True)
        scrollbar.pack(fill="x")

        treeviews.append(treeview)

        # 绑定事件
        combobox.bind("<<ComboboxSelected>>", lambda event, t=treeview, d=data, b=brand_label: on_combobox_change(event, t, d, b))

        update_treeview(treeview, data, default_furnace)

        # **初始化牌号显示**
        if default_furnace in data:
            latest_test = max(data[default_furnace].keys(), key=str)
            brand = data[default_furnace][latest_test].get("牌号", "未知")
            brand_label.config(text=f"牌号：{brand}")

        # **鼠标拖动框选多行**
        treeview.bind("<B1-Motion>", lambda event, t=treeview: on_mouse_drag_select(event, t))
        # 绑定右键菜单
        treeview.bind("<Button-3>", lambda event, t=treeview: show_context_menu(event, t))
        # **绑定 Ctrl+C 复制快捷键**
        treeview.bind("<Control-c>", lambda event, t=treeview: copy_selected_rows(t))

    # 启动自动刷新
    root.after(1000, lambda: auto_refresh(root, treeviews, comboboxes, brand_labels, countdown_label))

    # 启动数据处理线程
    script_thread = threading.Thread(target=run_external_scripts, daemon=True)
    script_thread.start()

    root.mainloop()

    
    
if __name__ == "__main__":
    create_gui()
