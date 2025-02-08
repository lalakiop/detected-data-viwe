import sys
import threading
import time
from PyQt5.QtWidgets import QHeaderView
# 从 PyQt5 库中导入所需的类，用于创建 GUI 界面
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QMenu
# 从 PyQt5 库中导入 QColor 类，用于设置颜色
from PyQt5.QtGui import QColor
# 从 PyQt5 库中导入 Qt 类和 QTimer 类，Qt 提供一些常量和枚举，QTimer 用于定时操作
from PyQt5.QtCore import Qt, QTimer
# 从 data_processing 模块中导入所需的函数，用于数据处理
from data_processing import process_folder, sotrjson, load_json_data, sort_furnace_tests

# 目标 JSON 文件路径，存储处理后的数据
json_files = ["data1.json", "data2.json", "data3.json"]
# 自动刷新间隔时间，单位为秒
refresh_interval = 120
# 倒计时初始值，用于自动刷新倒计时显示
countdown = refresh_interval
# txt 文件所在的文件夹路径，需要替换为实际路径
txtfolder_path = r"\\192.168.101.150\\cp"
# 处理后的数据保存的 JSON 文件
dataoutput_file = "data.json"

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
            # 等待指定的时间后再次执行循环
            time.sleep(refresh_interval)
        except Exception as e:
            print(f"运行外部脚本出错: {e}")

class MainWindow(QWidget):
    def __init__(self):
        # 调用父类 QWidget 的构造函数
        super().__init__()
        # 初始化界面
        self.initUI()
        # 启动自动刷新功能
        self.start_auto_refresh()
        # 启动数据处理线程，使用 daemon=True 表示该线程为守护线程，主线程退出时该线程也会退出
        script_thread = threading.Thread(target=run_external_scripts, daemon=True)
        script_thread.start()
        # 设置窗口的初始位置和大小
        self.setGeometry(500, 200, 1450, 1000)

    def initUI(self):
        # 设置窗口的标题
        self.setWindowTitle("炉号检测数据")
        # 创建一个垂直布局，用于管理界面元素的布局
        main_layout = QVBoxLayout()

        # 用于存储表格控件的列表
        self.tables = []
        # 用于存储下拉框控件的列表
        self.comboboxes = []
        # 用于存储牌号标签控件的列表
        self.brand_labels = []

        # 遍历目标 JSON 文件列表
        for i, json_file in enumerate(json_files):
            # 加载 JSON 文件中的数据
            data = load_json_data(json_file)

            # 对炉号进行排序，如果有数据则按降序排列，否则为空列表
            furnace_ids = sorted(data.keys(), key=int, reverse=True) if data else []
            # 获取默认的炉号，如果有数据则取第一个，否则为空字符串
            default_furnace = furnace_ids[0] if furnace_ids else ""

            # 创建一个垂直布局，用于管理每个炉号相关的界面元素
            sub_layout = QVBoxLayout()
            # 创建一个水平布局，用于管理炉号标签、下拉框和牌号标签
            top_layout = QHBoxLayout()

            # 创建一个标签，显示炉号编号
            label = QLabel(f"{i + 1}#炉")
            # 将标签添加到水平布局中
            top_layout.addWidget(label)

            # 创建一个下拉框
            combobox = QComboBox()
            # 向下拉框中添加炉号选项
            combobox.addItems(furnace_ids)
            # 设置下拉框的默认选中项
            combobox.setCurrentText(default_furnace)

            table = self.create_table()
            brand_label = self.create_brand_label()

            # 修正 lambda 表达式中的变量捕获问题
            combobox.currentTextChanged.connect(lambda text, t=table, d=data, l=brand_label: self.on_combobox_change(text, t, d, l))

            # 将下拉框添加到水平布局中
            top_layout.addWidget(combobox)
            # 将下拉框添加到下拉框列表中
            self.comboboxes.append(combobox)

            # 将牌号标签添加到水平布局中
            top_layout.addWidget(brand_label)
            # 将牌号标签添加到牌号标签列表中
            self.brand_labels.append(brand_label)

            # 将表格控件添加到表格列表中
            self.tables.append(table)

            # 将水平布局添加到垂直布局中
            sub_layout.addLayout(top_layout)
            # 将表格控件添加到垂直布局中
            sub_layout.addWidget(table)
            # 将垂直布局添加到主布局中
            main_layout.addLayout(sub_layout)

            # 更新表格的数据和牌号标签的显示
            self.update_table(table, data, default_furnace, brand_label)

        # 创建一个水平布局，用于管理刷新按钮和倒计时标签
        refresh_layout = QHBoxLayout()
        # 创建一个刷新按钮
        refresh_button = QPushButton("刷新")
        # 当刷新按钮被点击时，调用 refresh_data 方法刷新数据
        refresh_button.clicked.connect(self.refresh_data)
        # 创建一个倒计时标签，显示剩余的刷新时间
        self.countdown_label = QLabel(f"刷新倒计时: {countdown}s")
        # 将刷新按钮添加到水平布局中
        refresh_layout.addWidget(refresh_button)
        # 将倒计时标签添加到水平布局中
        refresh_layout.addWidget(self.countdown_label)
        # 将水平布局添加到主布局中
        main_layout.addLayout(refresh_layout)

        # 将主布局设置为窗口的布局
        self.setLayout(main_layout)

    def create_table(self):
        # 创建一个表格控件
        table = QTableWidget()
        # 设置表格的列数
        table.setColumnCount(16)
        # 设置表格的表头标签
        table.setHorizontalHeaderLabels(["炉号", "次数", "Si", "Cu", "Mg", "Fe", "Zn", "Ni", "Mn", "Ti", "Sn", "Pb", "Cr", "Al", "污泥指数", "时间"])
        # 设置表格的选择模式为扩展选择，允许选择多行
        table.setSelectionMode(QTableWidget.ExtendedSelection)
        # 设置表格的上下文菜单策略为自定义，允许显示右键菜单
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        # 当表格收到自定义上下文菜单请求时，调用 show_context_menu 方法显示右键菜单
        table.customContextMenuRequested.connect(self.show_context_menu)
        # 当表格收到按键事件时，调用 copy_selected_rows 方法处理复制操作
        table.keyPressEvent = lambda event            : self.copy_selected_rows(table, event)
        header = table.horizontalHeader()
        # 设置表头行高
        header.setDefaultSectionSize(50)

        # 调整表格内容自适应布局
        table.resizeColumnsToContents()
        table.resizeRowsToContents()  # 这里将表头行高设置为 40，可以根据需要调整
        # 设置默认行高
        table.verticalHeader().setDefaultSectionSize(35)

        # 可以单独设置每列的宽度，这里为了演示，统一设置列宽
        for col in range(table.columnCount()):
            table.setColumnWidth(col, 80)
        # 设置表格中时间列的宽度
        table.setColumnWidth(15, 200)
        
        

        return table

    def create_brand_label(self):
        # 创建一个牌号标签，初始显示为“牌号：未知”
        return QLabel("牌号：未知")

    def update_table(self, table, data, furnace_id, brand_label):
        table.setRowCount(0)
        if furnace_id in data:
            sorted_tests = sort_furnace_tests(data[furnace_id].keys())  # 按规则排序
            for test_num in sorted_tests:
                values = data[furnace_id][test_num]
                furnace_values = [furnace_id, test_num] + list(values.values())  # 组装数据

                # 获取 `牌号` 和 `Fe` 值
                brand = values.get("牌号", "")
                fe_value = values.get("Fe", 0)
                Pb_value = values.get("Pb", 0)                # 默认 0，避免 KeyError
                Cu_value = values.get("Cu", 0) 
                Si_value = values.get("Si", 0) 
                Mn_value = values.get("Mn", 0) 
                
                row_position = table.rowCount()
                table.insertRow(row_position)
                for col, value in enumerate(furnace_values):
                    item = QTableWidgetItem(str(value))
                    # 设置表格内容居中显示
                    item.setTextAlignment(Qt.AlignCenter)
                    if brand == "ADC12Z" and col == 5:  # 仅对 Fe 列（索引为 5）设置颜色
                        if 0.98 < fe_value < 1.00:
                            item.setForeground(QColor(255, 165, 0))
                        elif fe_value > 2.00:
                            item.setForeground(Qt.red)
                            
                    if brand == "ADC12Z" and col == 11:  # 仅对 Pb 列（索引为 11）设置颜色
                        if 0.09 < Pb_value <= 0.1:
                            item.setForeground(QColor(255, 165, 0))
                        elif Pb_value > 0.1:
                            item.setForeground(Qt.red)
                            
                    if brand == "ADC12Z" and col == 3:  # 仅对 Cu 列（索引为 3）设置颜色
                        if  Cu_value < 1.75 :
                            item.setForeground(QColor(0, 0, 255)) #设为蓝色
                        elif 1.75 <  Cu_value < 1.79 :
                            item.setForeground(QColor(203, 71, 255))#设为紫色
                        elif 2.3 > Cu_value > 2.0 :  
                            item.setForeground(QColor(255, 165, 0))  
                        elif Cu_value > 2.3 : 
                            item.setForeground(Qt.red)   
                    
                    if brand == "ADC12Z" and col == 2:  # 仅对 Si 列（索引为 3）设置颜色
                        if  Si_value < 10:
                            item.setForeground(QColor(0, 0, 255)) #设为蓝色
                        elif 10 <= Si_value < 10.2 :
                            item.setForeground(QColor(203, 71, 255))#设为紫色
                        elif 11.5 >= Si_value >= 11.2 :  
                            item.setForeground(QColor(255, 165, 0))  
                        elif Si_value > 11.5 : 
                            item.setForeground(Qt.red) 
                            
                    if brand == "ADC12Z" and col == 8:  # 仅对 Mn 列（索引为 3）设置颜色
                        if  Mn_value <= 0.2:
                            item.setForeground(QColor(0, 0, 255)) #设为蓝色
                        elif 0.2 < Mn_value < 0.22 :
                            item.setForeground(QColor(203, 71, 255))#设为紫色
                        elif 0.4 >= Mn_value >= 0.38 :  
                            item.setForeground(QColor(255, 165, 0))  
                        elif Mn_value > 0.4 : 
                            item.setForeground(Qt.red) 
                            
                    table.setItem(row_position, col, item)

            # 更新牌号
            latest_test = max(data[furnace_id].keys(), key=str)
            brand = data[furnace_id][latest_test].get("牌号", "未知")
            brand_label.setText(f"牌号：{brand}")

    def on_combobox_change(self, selected_furnace, table, data, brand_label):
        # 当下拉框的选中项改变时，更新表格的数据和牌号标签的显示
        self.update_table(table, data, selected_furnace, brand_label)

    def refresh_data(self):
        global countdown
        # 重置倒计时为初始值
        countdown = refresh_interval
        # 更新倒计时标签的显示
        self.update_countdown()

        # 遍历目标 JSON 文件列表
        for i, json_file in enumerate(json_files):
            # 加载 JSON 文件中的数据
            data = load_json_data(json_file)
            # 获取对应的下拉框控件
            combobox = self.comboboxes[i]
            # 获取对应的牌号标签控件
            brand_label = self.brand_labels[i]

            # 对炉号进行排序，如果有数据则按降序排列，否则为空列表
            furnace_ids = sorted(data.keys(), key=int, reverse=True) if data else []
            # 获取默认的炉号，如果有数据则取第一个，否则为空字符串
            default_furnace = furnace_ids[0] if furnace_ids else ""

            # 清空下拉框中的选项
            combobox.clear()
            # 向下拉框中添加炉号选项
            combobox.addItems(furnace_ids)
            # 设置下拉框的默认选中项
            combobox.setCurrentText(default_furnace)

            # 获取对应的表格控件
            table = self.tables[i]
            # 更新表格的数据和牌号标签的显示
            self.update_table(table, data, default_furnace, brand_label)

    def start_auto_refresh(self):
        # 创建一个定时器
        self.timer = QTimer(self)
        # 当定时器超时（每秒触发一次）时，调用 auto_refresh 方法
        self.timer.timeout.connect(self.auto_refresh)
        # 启动定时器，每隔 1000 毫秒（即 1 秒）触发一次
        self.timer.start(1000)

    def auto_refresh(self):
        global countdown
        if countdown > 0:
            # 倒计时减 1
            countdown -= 1
            # 更新倒计时标签的显示
            self.update_countdown()
        else:
            # 倒计时结束，刷新数据
            self.refresh_data()

    def update_countdown(self):
        # 更新倒计时标签的显示，显示剩余的刷新时间
        self.countdown_label.setText(f"刷新倒计时: {countdown}s")

    def copy_selected_rows(self, table, event):
        # 检查 event 是否为 None，如果为 None 则直接执行复制操作；如果不为 None 则检查是否按下了 Ctrl+C 组合键
        if event is None or (event.key() == Qt.Key_C and (event.modifiers() & Qt.ControlModifier)):
            # 获取表格中选中的所有项
            selected_items = table.selectedItems()
            if not selected_items:
                return

            # 获取选中项所在的行号，并进行排序
            rows = sorted(set(item.row() for item in selected_items))
            # 需要复制的列名
            columns = ["Si", "Cu", "Mg", "Fe", "Zn", "Ni", "Mn", "Ti", "Sn", "Pb", "Al"]
            # 获取需要复制的列的索引
            column_indexes = [table.horizontalHeaderItem(i).text() in columns for i in range(table.columnCount())]

            # 用于存储复制的数据
            copied_data = []
            # 遍历选中的行
            for row in rows:
                # 获取该行中需要复制的列的数据
                copied_values = [table.item(row, i).text() for i, col in enumerate(column_indexes) if col]
                # 将数据用制表符连接成字符串，并添加到复制数据列表中
                copied_data.append("\t".join(copied_values))

            # 将复制的数据用换行符连接成字符串
            clipboard_text = "\n".join(copied_data)
            # 将复制的数据设置到系统剪贴板中
            QApplication.clipboard().setText(clipboard_text)
            print("✅ 数据已复制到剪贴板！")

    def show_context_menu(self, pos):
        # 获取触发右键菜单的表格控件
        table = self.sender()
        # 创建一个上下文菜单
        context_menu = QMenu(self)
        # 在上下文菜单中添加一个“ADC12Z”选项，点击时调用 copy_selected_rows 方法进行复制操作
        context_menu.addAction("ADC12Z", lambda: self.copy_selected_rows(table, None))
        # 在上下文菜单中添加一个“ALSI10”选项，点击时调用 copy_selected_rows_alsi10 方法进行复制操作
        context_menu.addAction("ALSI10", lambda: self.copy_selected_rows_alsi10(table))
        # 在鼠标点击的位置显示上下文菜单
        context_menu.exec_(table.mapToGlobal(pos))

    def copy_selected_rows_alsi10(self, table):
        # 获取表格中选中的所有项
        selected_items = table.selectedItems()
        if not selected_items:
            return

        # 获取选中项所在的行号，并进行排序
        rows = sorted(set(item.row() for item in selected_items))
        # 需要复制的列名
        columns = ["Si", "Cu", "Mg", "Fe", "Zn", "Ni", "Mn", "Ti", "Sn", "Al"]
        # 获取需要复制的列的索引
        column_indexes = [table.horizontalHeaderItem(i).text() in columns for i in range(table.columnCount())]

        # 用于存储复制的数据
        copied_data = []
        # 遍历选中的行
        for row in rows:
            # 获取该行中需要复制的列的数据，并转换为浮点数
            row_values = [float(table.item(row, i).text()) for i, col in enumerate(column_indexes) if col]
            # 计算 100 减去所有元素值的和，并保留 4 位小数
            calculated_value = round(100 - sum(row_values), 4)
            # 将计算结果插入到数据列表中
            copied_values = row_values[:-1] + [calculated_value, row_values[-1]]
            # 将数据用制表符连接成字符串，并添加到复制数据列表中
            copied_data.append("\t".join(map(str, copied_values)))

        # 将复制的数据用换行符连接成字符串
        clipboard_text = "\n".join(copied_data)
        # 将复制的数据设置到系统剪贴板中
        QApplication.clipboard().setText(clipboard_text)
        print("✅ 数据已复制到剪贴板！")


if __name__ == "__main__":
    # 创建一个 QApplication 实例，用于管理应用程序的资源和事件循环
    app = QApplication(sys.argv)
    # 创建主窗口实例
    window = MainWindow()
    # 显示主窗口
    window.show()
    # 进入应用程序的主事件循环，等待用户操作
    sys.exit(app.exec_())