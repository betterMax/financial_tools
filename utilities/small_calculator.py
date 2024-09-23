import tkinter as tk
from tkinter import messagebox


def calculate():
    try:
        num1 = float(entry1.get())
        num2 = float(entry2.get())

        # 确保第一个数字为大数，第二个数字为小数
        larger = max(num1, num2)
        smaller = min(num1, num2)

        # 计算 (大数 - 小数) / 小数
        result = (larger - smaller) / smaller
        result_label.config(text=f"结果: {result:.2f}")
    except ValueError:
        messagebox.showerror("输入错误", "请输入有效的数字！")


# 绑定回车键事件
def on_enter(event):
    calculate()


# 创建主窗口
root = tk.Tk()
root.title("简单计算器")
root.geometry("300x300")

# 窗口始终置顶
root.attributes('-topmost', True)

# 标签和输入框
label1 = tk.Label(root, text="请输入第一个数字:")
label1.pack(pady=5)
entry1 = tk.Entry(root)
entry1.pack(pady=5)

label2 = tk.Label(root, text="请输入第二个数字:")
label2.pack(pady=5)
entry2 = tk.Entry(root)
entry2.pack(pady=5)

# 绑定回车键到输入框
entry1.bind("<Return>", on_enter)
entry2.bind("<Return>", on_enter)

# 计算按钮
calc_button = tk.Button(root, text="计算", command=calculate)
calc_button.pack(pady=10)

# 结果标签
result_label = tk.Label(root, text="结果: ")
result_label.pack(pady=5)

# 运行主循环
root.mainloop()
