from tasks import update_qihuo_price, update_qihuo_main, update_stock_price, update_qihuo_history
from config import Input_Path, Output_Path
import time


def main():
    # 程序开始时记录时间
    start_time = time.time()
    # 询问用户要运行哪些任务，并获取逗号分隔的任务编号
    tasks_str = input("请选择要执行的任务（1-任务1，2-任务2，3-任务3，4-任务4，all-全部任务。多个任务请用逗号分隔）：")

    # 如果用户输入 'all'，则运行所有任务
    if tasks_str.lower() == 'all':
        tasks = ['1', '2', '3', '4']
    else:
        # 根据逗号分隔任务编号，并移除可能存在的空格
        tasks = [task.strip() for task in tasks_str.split(',')]

    mode = 'work'
    if '1' in tasks or '3' in tasks:
        mode = input("请输入想要使用的模式：")

    # 对于每个任务编号，运行相应的任务
    for task in tasks:
        if task == '1':
            input_path = Input_Path
            output_path = Output_Path
            update_qihuo_price.run(input_path, output_path, mode)
        elif task == '2':
            file_path = Output_Path
            update_qihuo_main.run(file_path)
        elif task == '3':
            input_path = Input_Path
            output_path = Output_Path
            update_stock_price.run(input_path, output_path, mode)
        elif task == '4':
            input_path = Input_Path
            output_path = Output_Path
            update_qihuo_history.run(input_path, output_path)

        else:
            print(f"无效的选择：{task}")
    # 程序结束时记录时间
    end_time = time.time()

    # 计算运行时间
    elapsed_time = end_time - start_time

    # 转换为分钟和秒
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    # 打印结果
    print(f"运行时间：{minutes}分{seconds}秒")

if __name__ == '__main__':
    main()
