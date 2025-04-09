# -*- encoding: utf-8 -*-
'''
@File    :   start_app.py
@Author  :   编程学习园地 
@License :   该项目受专利、软著保护，仅供个人学习使用，严禁倒卖，一经发现，编程学习园地团队有必要追究法律责任！！！
'''


import os
import sys
import platform

parent = os.path.dirname(os.path.abspath(__file__))
if parent not in sys.path:
    sys.path.append(parent)

credentials_file_path=os.path.join(os.path.expanduser("~"), ".streamlit", "credentials.toml")
if os.path.exists(credentials_file_path):
    pass
else:
    os.makedirs(os.path.dirname(credentials_file_path))
    data = {"email": ''}
    import toml
    with open(credentials_file_path, "w") as f:
        toml.dump({"general": data}, f)
sys_type=platform.system()
def check_path():
    project_path=''  
    if sys_type=='Windows':
        project_path=str(os.getcwd()).split('\\')
    if sys_type=='Linux' or sys_type=='Darwin':
        project_path=str(os.getcwd()).split('/')
    for index,ch in enumerate(project_path):
        if index==0:
            continue
        else:
            ch=ch.replace('_','')
            if not ch.encode().isalnum():
                return False
    return True
        
if __name__=='__main__':
    if not check_path():
        if sys_type=='Windows' or sys_type=='Darwin':
            import tkinter as tk
            from tkinter import messagebox
            tk.messagebox.showerror('项目路径非法',f"项目路径异常!!!项目当前所在目录:{os.getcwd()} 路径非法!路径必须为全英文或者英文与数字、下划线的组合,不能存在任何特殊字符!否则项目功能异常!请更换项目目录或者修改当前目录为全英文,然后重新启动项目!")
        else:
            print(f"项目路径异常!!!项目当前所在目录:{os.getcwd()} 路径非法!路径必须为全英文或者英文与数字、下划线的组合,不能存在任何特殊字符!否则项目功能异常!请更换项目目录或者修改当前目录为全英文,然后重新启动项目!")
        sys.exit()
           
    command = 'python -m streamlit run app.py --server.enableCORS true'
    os.system(command)