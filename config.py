# -*- encoding: utf-8 -*-
'''
@File    :   config.py
@Author  :   编程学习园地 
@License :   该项目受专利、软著保护，仅供个人学习使用，严禁倒卖，一经发现，编程学习园地团队有必要追究法律责任！！！
'''


import os
import sys
from pathlib import Path


#获取当前文件的绝对路径
file_path = Path(__file__).resolve()

#获取当前文件的上一级目录的路径
root_path = file_path.parent

#如果当前文件的父目录不在搜索路径中则添加进去
if root_path not in sys.path:
    sys.path.append(str(root_path))

#获取当前项目(工作目录)的相对路径
ROOT = root_path.relative_to(Path.cwd())
MODEL_DIR = ROOT / 'weights'
#注意：如果你想要加载自己训练的模型(yolov5、v8微调版本(必须是通过ultralytics训练),这些都支持,修改了网络结构的不支持;且要注意模型训练版本与推理版本所使用的ultralytics相同)
# 只需将自己的模型放在weights目录下,系统界面'模型选择'下拉框会显示出新模型，届时可以手动选择模型

#侧边栏模型选择列表
MODEL_LIST=[]

weights=os.listdir(MODEL_DIR)

for weight in weights:
    MODEL_LIST.append(weight)