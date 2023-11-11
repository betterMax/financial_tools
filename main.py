from tasks import update_qihuo_price, update_qihuo_main, update_stock_price
from config import EXCEL_PATH1, EXCEL_PATH2, EXCEL_PATH3
import time


def main():
    # 询问用户要运行哪些任务，并获取逗号分隔的任务编号
    tasks_str = input("请选择要执行的任务（1-任务1，2-任务2，3-任务3，all-全部任务。多个任务请用逗号分隔）：")

    # 如果用户输入 'all'，则运行所有任务
    if tasks_str.lower() == 'all':
        tasks = ['1', '2', '3']
    else:
        # 根据逗号分隔任务编号，并移除可能存在的空格
        tasks = [task.strip() for task in tasks_str.split(',')]

    # 对于每个任务编号，运行相应的任务
    for task in tasks:
        if task == '1':
            file_path = EXCEL_PATH1
            mode = input("请输入想要使用的模式：")
            update_qihuo_price.run(file_path, mode)
        elif task == '2':
            file_path = EXCEL_PATH2
            update_qihuo_main.run(file_path)
        elif task == '3':
            file_path = EXCEL_PATH3
            mode = input("请输入想要使用的模式：")
            update_stock_price.run(file_path, mode)
        else:
            print(f"无效的选择：{task}")
    print(time.time())

if __name__ == '__main__':
    main()
