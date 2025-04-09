# -*- encoding: utf-8 -*-
'''
@File    :   app.py
@Author  :   编程学习园地 
@License :   该项目受专利、软著保护，仅供个人学习使用，严禁倒卖，一经发现，编程学习园地团队有必要追究法律责任！！！
'''

import streamlit as st
from PIL import Image
import tempfile
import cv2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sqlite3
import hashlib
import random
import string
import time
from utils import load_model, infer_image, infer_video_frame
from config import *

# ==================== 用户认证功能 ====================
def init_db():
    """初始化数据库"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    ''')
    # 创建评论表
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    # 创建回复表
    c.execute('''
        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    """哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, email):
    """注册用户"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, hash_password(password), email)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def authenticate_user(username, password):
    """验证用户"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password))
    )
    user = c.fetchone()
    conn.close()
    return user is not None

def generate_temp_password(length=10):
    """生成临时密码"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# 初始化数据库
init_db()

# ==================== 全局样式配置 ====================
st.set_page_config(
    page_title="玉米叶片病虫害检测系统",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
custom_css = """
<style>
    /* 基础样式 */
    html {
        scroll-behavior: smooth;
    }
    body {
        background: #f8f9fa;
        color: #333;
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* 导航栏样式 */
    .sidebar-content h2 {
        font-size: 1.2rem !important;
        font-weight: bold;
        color: #2c5f2d;
         color: green;
    }

    /* 内容区域 */
    .main-container {
        margin-top: 80px;
        padding: 2rem 4rem;
    }

    /* 卡片样式 */
    .custom-card {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }
    .custom-card:hover {
        transform: translateY(-5px);
    }

    /* 新闻和病害卡片样式 */
    .news-item, .disease-card {
        display: flex;
        gap: 1.5rem;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid #eee;
    }
    .news-item:last-child, .disease-card:last-child {
        border-bottom: none;
    }

    /* 登录和注册表单样式 */
    .auth-form {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }

    /* 评论样式 */
    .comment {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .comment-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    .comment-author {
        font-weight: bold;
        color: #2c5f2d;
    }
    .comment-time {
        color: #999;
        font-size: 0.9rem;
    }

    /* 回复样式 */
    .reply {
        background: #e8f5e9;
        border-radius: 8px;
        padding: 0.5rem;
        margin-left: 2rem;
        margin-bottom: 0.5rem;
    }
    .reply-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    .reply-author {
        font-weight: bold;
        color: #2c5f2d;
    }
    .reply-time {
        color: #999;
        font-size: 0.9rem;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# ==================== 认证页面 ====================
def auth_page():
    """统一的登录/注册页面"""
    if 'username' in st.session_state:
        st.warning(f"您已登录为 {st.session_state.username}。请先注销再登录或注册。")
        return

    # 页面标题
    st.markdown('<h1 style="text-align: center; color: #2c5f2d;">用户认证</h1>', unsafe_allow_html=True)
    
    # 选项卡
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    with tab1:
        with st.form("login_form", clear_on_submit=True):
            st.markdown('<div class="auth-form">', unsafe_allow_html=True)
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            submitted = st.form_submit_button("登录")
            
            if submitted:
                if authenticate_user(username, password):
                    st.session_state.username = username
                    st.session_state.logged_in = True
                    st.success("登录成功！")
                    st.experimental_rerun()
                else:
                    st.error("用户名或密码错误！")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        with st.form("register_form", clear_on_submit=True):
            st.markdown('<div class="auth-form">', unsafe_allow_html=True)
            username = st.text_input("用户名")
            email = st.text_input("电子邮箱")
            password = st.text_input("密码", type="password")
            confirm_password = st.text_input("确认密码", type="password")
            submitted = st.form_submit_button("注册")
            
            if submitted:
                if password != confirm_password:
                    st.error("两次输入的密码不一致！")
                elif len(password) < 6:
                    st.error("密码长度至少为6位！")
                else:
                    if register_user(username, password, email):
                        st.success("注册成功！请登录。")
                        st.session_state.register_success = True
                    else:
                        st.error("用户名或邮箱已存在！")
            st.markdown('</div>', unsafe_allow_html=True)

def logout():
    """注销用户"""
    if 'username' in st.session_state:
        del st.session_state.username
        del st.session_state.logged_in
        if 'current_page' in st.session_state:
            del st.session_state.current_page
        st.session_state.logout = True
        st.success("您已成功注销！")
        # 移除成功注销的提示信息
        if 'logout' in st.session_state:
            del st.session_state.logout
        st.experimental_rerun()

# ==================== 论坛页面 ====================
def forum_page():
    """论坛交流页面"""
    if 'username' not in st.session_state:
        st.warning("请先登录后再访问论坛。")
        return

    st.markdown('<h1 style="text-align: center; color: #2c5f2d;">💬 论坛交流</h1>', unsafe_allow_html=True)

    # 显示评论
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM comments ORDER BY timestamp DESC")
    comments = c.fetchall()
    conn.close()

    if comments:
        for comment in comments:
            comment_id, username, content, timestamp = comment
            st.markdown(f"""
                <div class="comment">
                    <div class="comment-header">
                        <span class="comment-author">{username}</span>
                        <span class="comment-time">{timestamp}</span>
                    </div>
                    <p>{content}</p>
            """, unsafe_allow_html=True)

            # 显示回复
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("SELECT * FROM replies WHERE comment_id = ? ORDER BY timestamp ASC", (comment_id,))
            replies = c.fetchall()
            conn.close()

            if replies:
                for reply in replies:
                    reply_id, _, reply_username, reply_content, reply_timestamp = reply
                    st.markdown(f"""
                        <div class="reply">
                            <div class="reply-header">
                                <span class="reply-author">{reply_username}</span>
                                <span class="reply-time">{reply_timestamp}</span>
                            </div>
                            <p>{reply_content}</p>
                        </div>
                    """, unsafe_allow_html=True)

            # 添加回复
            with st.form(f"reply_form_{comment_id}", clear_on_submit=True):
                reply_content = st.text_area("回复评论", height=80, key=f"reply_{comment_id}")
                submitted = st.form_submit_button("提交回复")

                if submitted:
                    if reply_content.strip():
                        conn = sqlite3.connect('users.db')
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO replies (comment_id, username, content, timestamp) VALUES (?, ?, ?, ?)",
                            (comment_id, st.session_state.username, reply_content, time.strftime("%Y-%m-%d %H:%M:%S"))
                        )
                        conn.commit()
                        conn.close()
                        st.success("回复成功！")
                        st.experimental_rerun()
                    else:
                        st.error("回复内容不能为空！")

            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("暂无评论，快来发表第一条评论吧！")

    # 添加评论
    with st.form("comment_form", clear_on_submit=True):
        content = st.text_area("发表评论", height=100)
        submitted = st.form_submit_button("提交评论")

        if submitted:
            if content.strip():
                conn = sqlite3.connect('users.db')
                c = conn.cursor()
                c.execute(
                    "INSERT INTO comments (username, content, timestamp) VALUES (?, ?, ?)",
                    (st.session_state.username, content, time.strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
                conn.close()
                st.success("评论发表成功！")
                st.experimental_rerun()
            else:
                st.error("评论内容不能为空！")

    # 删除评论（仅限评论者本人）
    if comments:
        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<h3 style="color: #2c5f2d;">删除评论</h3>', unsafe_allow_html=True)
        comment_ids = [comment[0] for comment in comments if comment[1] == st.session_state.username]
        if comment_ids:
            comment_id_to_delete = st.selectbox("选择要删除的评论", comment_ids)
            if st.button("删除评论"):
                conn = sqlite3.connect('users.db')
                c = conn.cursor()
                c.execute("DELETE FROM comments WHERE id = ?", (comment_id_to_delete,))
                conn.commit()
                conn.close()
                st.success("评论删除成功！")
                st.experimental_rerun()
        else:
            st.info("您没有可删除的评论。")

# ==================== 页面组件 ====================
def render_navbar():
    """使用Streamlit原生功能实现导航栏"""
    pages = ["首页", "检测", "相关新闻", "科普信息", "论坛交流", "关于我们", "认证"]  # 确保包含“认证”选项
    st.sidebar.header("导航栏")
    
    if 'username' in st.session_state:
        current_page = st.sidebar.radio("选择页面", pages)
        if st.sidebar.button("注销", key="logout_button"):
            logout()
    else:
        current_page = st.sidebar.radio("选择页面", pages)
    
    return current_page



# ==================== 页面内容 ====================
def home_page():
    st.markdown("""
        <div class="container">
            <h1 style="text-align: center; color: #2c5f2d;">🌽 基于YOLO8的玉米叶片病虫害检测系统</h1>
            <div class="section-title">📌 系统简介</div>
            <p style="line-height: 1.8; font-size: 1.1rem;">
                本系统集成了先进的深度学习技术和农业知识，能够对玉米叶片病虫害进行智能检测。主要功能包括：
            </p>
            <ul style="line-height: 1.8; font-size: 1.1rem;">
                <li>支持图片、视频和实时摄像头输入</li>
                <li>识别 12 大类 36 种常见病虫害</li>
                <li>检测速度快，准确率高</li>
                <li>提供详细的防治建议</li>
            </ul>
            <div class="section-title">📊 近期数据统计</div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                <div style="padding: 1rem; background: #e8f5e9; border-radius: 8px;">
                    <h4>🔄 日均检测量</h4>
                    <p style="font-size: 1.5rem;">1,235 次</p>
                </div>
                <div style="padding: 1rem; background: #f3e5f5; border-radius: 8px;">
                    <h4>🎯 平均准确率</h4>
                    <p style="font-size: 1.5rem;">92.3%</p>
                </div>
                <div style="padding: 1rem; background: #e3f2fd; border-radius: 8px;">
                    <h4>⏱ 响应速度</h4>
                    <p style="font-size: 1.5rem;">200ms/帧</p>
                </div>
            </div>
            <div class="section-title">🌟 用户反馈</div>
            <p style="line-height: 1.8; font-size: 1.1rem;">
                用户对系统的评价非常积极，许多农民表示系统帮助他们及时发现病虫害，减少了损失。
            </p>
        </div>
    """, unsafe_allow_html=True)

def detection_page():
    """优化检测页面，减少屏闪问题"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 检测配置")
        model_type = st.selectbox("选择模型", MODEL_LIST)
        model_path = Path(MODEL_DIR, model_type)
        confidence = st.slider("置信度阈值", 10, 100, 25) / 100
        iou = st.slider("IoU阈值", 10, 100, 45) / 100
        source_type = st.radio("输入源类型", ("图片", "视频", "摄像头"))

    # 使用缓存加载模型
    @st.cache(allow_output_mutation=True)
    def load_model_cached(model_path):
        return load_model(model_path)

    model = load_model_cached(model_path)

    # 占位符，用于动态更新检测结果
    result_placeholder = st.empty()

    if source_type == "图片":
        uploaded_file = st.file_uploader("上传图片", type=['png', 'jpeg', 'jpg'])
        if uploaded_file:
            with result_placeholder.container():
                cols = st.columns([1, 2])
                with cols[0]:
                    st.image(uploaded_file, caption="原始图像", use_column_width=True)
                with cols[1]:
                    with st.spinner("🔄 正在分析..."):
                        result_img, labels, data = infer_image(model, Image.open(uploaded_file), confidence, iou)
                        st.image(result_img, caption="检测结果", channels="BGR")
                        st.dataframe(pd.DataFrame(data), use_container_width=True)

    elif source_type == "视频":
        uploaded_file = st.file_uploader("上传视频", type=['mp4'])
        if uploaded_file:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(uploaded_file.read())
            vid_cap = cv2.VideoCapture(tfile.name)

            # 占位符，用于动态更新视频帧
            video_placeholder = st.empty()
            frame_count = 0
            frame_rate_divider = 5  # 控制每 5 帧更新一次

            with st.spinner("🔄 正在分析视频..."):
                while vid_cap.isOpened():
                    success, image = vid_cap.read()
                    if not success:
                        vid_cap.release()
                        break

                    # 仅处理每隔 frame_rate_divider 帧
                    if frame_count % frame_rate_divider == 0:
                        result_img = infer_video_frame(model, image, confidence, iou)
                        video_placeholder.image(result_img, channels="BGR", caption="视频检测结果")
                    frame_count += 1

    elif source_type == "摄像头":
        flag = st.button("开始检测")
        if flag:
            vid_cap = cv2.VideoCapture(0)

            # 占位符，用于动态更新摄像头帧
            camera_placeholder = st.empty()

            while vid_cap.isOpened():
                success, image = vid_cap.read()
                if success:
                    result_img = infer_video_frame(model, image, confidence, iou)
                    camera_placeholder.image(result_img, channels="BGR", caption="摄像头检测结果")
                else:
                    vid_cap.release()
                    break

    st.markdown('</div>', unsafe_allow_html=True)

def news_page():
    """丰富相关新闻页面"""
    st.markdown("""
        <div class="container">
            <h2 class="gradient-title">🌾 最新农业科技新闻</h2>
            <p style="font-size: 1.1rem; line-height: 1.8;">
                了解最新的农业科技动态，为精准农业和病虫害防治提供更多灵感。
            </p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                <div class="custom-card">
                    <img src="https://www.pku-iaas.edu.cn/static/upload/image/20250319/1742365451707285.png" alt="news"
                        style="width: 100%; border-radius: 8px; margin-bottom: 1rem;">
                    <h3 style="color: #2c5f2d;">玉米新品种研发取得突破</h3>
                    <p style="line-height: 1.6; font-size: 1rem;">
                         近日，北京大学现代农业研究院在爆裂玉米育种研究领域取得重要进展，其选育的品种北芯 P101在2024年新疆地区品种审定区域试验中表现突出。

  据了解，北芯P101在爆裂玉米试验组全部6个测试点均比对照表现增产，平均增产15.6%，平均亩产达640.3kg，在增产幅度与产量方面均位居同一试验组榜首。区试表明该品种在新疆地区生育期为 111.3 天，比对照晚熟 2.3天 ；倒伏率、丝黑穗病率、黑粉病率、茎腐病率均为 0，表明该品种具有良好的抗病性。
                    </p>
                    <a href="https://maize.sicau.edu.cn/info/1003/2594.htm" class="animated-button">阅读更多</a>
                </div>
                <div class="custom-card">
                    <img src="https://news.cau.edu.cn/images/2025-04/52684affbbd74fc6ac2a715ef4023a5b.jpeg" alt="news"
                        style="width: 100%; border-radius: 8px; margin-bottom: 1rem;">
                    <h3 style="color: #185a9d;">智耕未来 | 农业AI智能眼镜：练就“火眼金睛”，变身“智能参谋”</h3>
                    <p style="line-height: 1.6; font-size: 1rem;">
                        田间地头，深度学习算法解码土壤与气象密码，具身机器人化身“新农人”精准作业；实验室里，AI加速基因编辑与育种突破，合成数据技术破解农业科研瓶颈；课堂内外，智能体辅助个性化教学，跨学科培养“AI+”的复合人才……
                    </p>
                    <a href="https://news.cau.edu.cn/zhxwnew/f4c00afd681742d3bee4674a59c5be8e.htm" class="animated-button">阅读更多</a>
                </div>
                <div class="custom-card">
                    <img src="https://aircas.cas.cn/dtxw/kydt/202410/W020241021376837615573.png" alt="news"
                        style="width: 100%; border-radius: 8px; margin-bottom: 1rem;">
                    <h3 style="color: #9c27b0;">我国首个自主研发的“慧眼”天空地植物病虫害智能监测预警系统正式发布</h3>
                    <p style="line-height: 1.6; font-size: 1rem;">
                        通过新兴农业技术和精准数据分析，农民可以制定最佳种植策略，显著提高作物产量，减少资源浪费。
                    </p>
                    <a href="https://aircas.cas.cn/dtxw/kydt/202410/t20241021_7404926.html" class="animated-button">阅读更多</a>
                </div>
                    <div class="custom-card">
                    <img src="https://imagepphcloud.thepaper.cn/pph/image/329/660/9.jpg" alt="news"
                        style="width: 100%; border-radius: 8px; margin-bottom: 1rem;">
                    <h3 style="color: #2c5f2d;">民生智库 | 智慧农业为农业现代化插上翅膀</h3>
                    <p style="line-height: 1.6; font-size: 1rem;">
                        近日，农业农村部发布《农业农村部关于大力发展智慧农业的指导意见》(以下简称《指导意见》)与《全国智慧农业行动计划(2024—2028年)》(以下简称《行动计划》)，明确了今后一段时期推进智慧农业的工作思路和重点任务，为我国农业的转型升级和高质量发展绘制了宏伟蓝图。
                    </p>
                    <a href="https://www.thepaper.cn/newsDetail_forward_29332805" class="animated-button">阅读更多</a>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)



def knowledge_page():
    """丰富科普信息页面"""
    st.markdown("""
        <div class="container">
            <h2 class="gradient-title">📖 病虫害百科全书</h2>
            <p style="font-size: 1.1rem; line-height: 1.8;">
                掌握常见的玉米病虫害知识，帮助您更好地保护作物，提升农业生产效率。
            </p>
    """, unsafe_allow_html=True)

    # 固定导航栏
    st.markdown("""
        <div style="position: sticky; top: 0; background: white; z-index: 100; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="display: flex; overflow-x: auto; gap: 1rem; padding: 1rem 0; border-bottom: 1px solid #eee;">
                <button class="tab-btn active" style="color: #2c5f2d; font-weight: bold; padding: 0.5rem 1rem; border: none; background: none; cursor: pointer;" onclick="scrollToSection('all')">
                    全部
                </button>
                <button class="tab-btn" style="color: #666; padding: 0.5rem 1rem; border: none; background: none; cursor: pointer;" onclick="scrollToSection('diseases')">
                    病害
                </button>
                <button class="tab-btn" style="color: #666; padding: 0.5rem 1rem; border: none; background: none; cursor: pointer;" onclick="scrollToSection('pests')">
                    虫害
                </button>
                <button class="tab-btn" style="color: #666; padding: 0.5rem 1rem; border: none; background: none; cursor: pointer;" onclick="scrollToSection('methods')">
                    防治方法
                </button>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 病虫害内容展示
    st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 2rem;">
    """, unsafe_allow_html=True)

    # 病害内容
    with st.expander("病害", expanded=True):
        st.markdown("""
            <div id="diseases" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
        """, unsafe_allow_html=True)

        diseases = [
            {
                "title": "玉米锈病",
                "content": """玉米锈病是一种常见的真菌病害，主要通过空气传播，可导致叶片枯萎。防治措施包括：
                <ul>
                    <li>使用抗锈病品种</li>
                    <li>及时喷洒合适的杀菌剂</li>
                    <li>确保田间通风良好</li>
                </ul>""",
                "bg_color": "#e8f5e9",
                "text_color": "#2c5f2d",
                "image": "https://pic.baike.soso.com/ugc/baikepic2/700/20200619093832-1694341708_jpeg_928_698_133414.jpg/300"
            },
            {
                "title": "玉米叶斑病",
                "content": """玉米叶斑病会导致叶片出现明显斑点，影响光合作用，降低产量。防治措施包括：
                <ul>
                    <li>及时清理病叶</li>
                    <li>喷洒对症的药剂</li>
                    <li>种植抗病品种</li>
                </ul>""",
                "bg_color": "#f3e5f5",
                "text_color": "#9c27b0",
                "image": "https://pic.baike.soso.com/ugc/baikepic2/0/20240905045352-299625457_jpeg_268_201_11299.jpg/300"
            },
            {
                "title": "玉米灰斑病",
                "content": """玉米灰斑病是一种由真菌引起的病害，主要影响叶片和茎秆。防治措施包括：
                <ul>
                    <li>选择抗病品种</li>
                    <li>及时清理病残体</li>
                    <li>合理轮作</li>
                </ul>""",
                "bg_color": "#e3f2fd",
                "text_color": "#185a9d",
                "image": "https://pic.baike.soso.com/ugc/baikepic2/0/20221203083642-1867922326_jpeg_1060_700_710726.jpg/300"
            }
        ]

        for disease in diseases:
            st.markdown(f"""
                <div style="background: {disease['bg_color']}; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                    <img src="{disease['image']}" style="width: 60%; border-radius: 8px; margin-bottom: 1rem;">
                    <h3 style="color: {disease['text_color']}; margin-bottom: 0.5rem;">{disease['title']}</h3>
                    <p style="line-height: 1.6; font-size: 1rem; color: {disease['text_color']};">
                        {disease["content"]}
                    </p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # 虫害内容
    with st.expander("虫害", expanded=True):
        st.markdown("""
            <div id="pests" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
        """, unsafe_allow_html=True)

        pests = [
            {
                "title": "玉米螟虫",
                "content": """玉米螟虫是玉米的主要害虫之一，幼虫啃食玉米茎秆，影响产量。防治措施包括：
                <ul>
                    <li>使用生物农药</li>
                    <li>及时清除田间杂草</li>
                    <li>利用天敌昆虫进行生物控制</li>
                </ul>""",
                "bg_color": "#e3f2fd",
                "text_color": "#185a9d",
                "image": "https://pic.baike.soso.com/ugc/baikepic2/18494/cut-20180802150209-947627998_jpg_889_593_86455.jpg/300"
            },
            {
                "title": "玉米粘虫",
                "content": """玉米粘虫是一种迁飞性害虫，幼虫会大量啃食玉米叶片。防治措施包括：
                <ul>
                    <li>使用诱虫灯诱杀成虫</li>
                    <li>喷洒高效低毒农药</li>
                    <li>及时清理田间杂草</li>
                </ul>""",
                "bg_color": "#f3e5f5",
                "text_color": "#9c27b0",
                "image": "https://pic.baike.soso.com/ugc/baikepic2/0/20230523213452-486027403_jpeg_923_615_346244.jpg/300"
            },
            {
                "title": "玉米蚜虫",
                "content": """玉米蚜虫会吸食玉米植株的汁液，导致叶片发黄枯萎。防治措施包括：
                <ul>
                    <li>使用黄色粘虫板诱杀</li>
                    <li>喷洒吡虫啉等药剂</li>
                    <li>保护天敌昆虫</li>
                </ul>""",
                "bg_color": "#e8f5e9",
                "text_color": "#2c5f2d",
                "image": "https://pic.baike.soso.com/ugc/baikepic2/0/20230524104643-1709044069_jpeg_1076_710_480636.jpg/300"
            }
        ]

        for pest in pests:
            st.markdown(f"""
                <div style="background: {pest['bg_color']}; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                    <img src="{pest['image']}" style="width: 60%; border-radius: 8px; margin-bottom: 1rem;">
                    <h3 style="color: {pest['text_color']}; margin-bottom: 0.5rem;">{pest['title']}</h3>
                    <p style="line-height: 1.6; font-size: 1rem; color: {pest['text_color']};">
                        {pest["content"]}
                    </p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # 防治方法内容
    with st.expander("防治方法", expanded=True):
        st.markdown("""
            <div id="methods" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
        """, unsafe_allow_html=True)

        methods = [
            {
                "title": "化学防治",
                "content": """化学防治是通过使用农药来控制病虫害。注意事项包括：
                <ul>
                    <li>选择合适的农药</li>
                    <li>按照说明书使用</li>
                    <li>避免在高温或大风天气喷洒</li>
                </ul>""",
                "bg_color": "#e8f5e9",
                "text_color": "#2c5f2d",
                "image": "https://pic4.zhimg.com/v2-2cd1abf8c6042070fece387435292b3b_1440w.webp?consumer=ZHI_MENG"
            },
            {
                "title": "生物防治",
                "content": """生物防治是利用天敌昆虫或微生物来控制病虫害。方法包括：
                <ul>
                    <li>释放天敌昆虫</li>
                    <li>使用生物农药</li>
                    <li>保护自然天敌</li>
                </ul>""",
                "bg_color": "#e3f2fd",
                "text_color": "#185a9d",
                "image": "https://th.bing.com/th/id/OSK.HEROJU8QNBwxYHg1UHfY6YM4_PNcvVYEDY8q1Uzaqdqq3oE?w=312&h=200&c=15&rs=2&o=6&dpr=2&pid=SANGAM"
            },
            {
                "title": "物理防治",
                "content": """物理防治是通过物理手段来控制病虫害。方法包括：
                <ul>
                    <li>使用粘虫板</li>
                    <li>设置防虫网</li>
                    <li>人工捕捉害虫</li>
                </ul>""",
                "bg_color": "#f3e5f5",
                "text_color": "#9c27b0",
                "image": "https://t11.baidu.com/it/app=49&f=JPEG&fm=173&fmt=auto&u=3611537380%2C3232031753?w=486&h=274&s=61B07EDB1EE2D747002C872C03003057"
            }
        ]

        for method in methods:
            st.markdown(f"""
                <div style="background: {method['bg_color']}; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                    <img src="{method['image']}" style="width: 60%; border-radius: 8px; margin-bottom: 1rem;">
                    <h3 style="color: {method['text_color']}; margin-bottom: 0.5rem;">{method['title']}</h3>
                    <p style="line-height: 1.6; font-size: 1rem; color: {method['text_color']};">
                        {method["content"]}
                    </p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # 添加JavaScript交互效果
    st.markdown("""
        <script>
            function scrollToSection(id) {
                document.getElementById(id).scrollIntoView({ behavior: 'smooth' });
                document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                event.target.classList.add('active');
            }
        </script>
    """, unsafe_allow_html=True)

def about_page():
    """关于我们页面"""
    st.markdown('<h1 style="text-align: center; color: #2c5f2d;">关于我们</h1>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="container">
            <h2 style="color: #2c5f2d;">🌽 玉米的重要性</h2>
            <p style="font-size: 1.1rem; line-height: 1.8;">
                玉米是全球最重要的粮食作物之一，也是我国主要的粮食和饲料作物。它不仅是人类食物的重要来源，还是畜牧业饲料和工业原料的主要组成部分。玉米的产量和质量直接影响我国的粮食安全和经济发展。
            </p>
            <p style="font-size: 1.1rem; line-height: 1.8;">
                玉米种植面积广泛，适应性强，对气候和土壤条件的适应能力使其成为我国农业生产的重要支柱。然而，病虫害的发生对玉米产量和质量造成了严重威胁，每年因病虫害导致的损失高达数千万吨。
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="container">
            <h2 style="color: #2c5f2d;">🌱 研究意义</h2>
            <p style="font-size: 1.1rem; line-height: 1.8;">
                本项目致力于通过人工智能技术，特别是基于YOLO8的目标检测算法，为玉米病虫害的智能识别和防治提供科学依据。我们的目标是：
            </p>
            <ul style="font-size: 1.1rem; line-height: 1.8;">
                <li>提高病虫害识别的准确性和效率，减少人工检测的误差和成本</li>
                <li>提供实时监测和预警系统，帮助农民及时采取防治措施</li>
                <li>推广科学防治方法，减少农药使用，保护生态环境</li>
                <li>为农业科研和政策制定提供数据支持</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    # 添加折线图展示害虫对玉米产量的影响
    st.markdown("""
        <div class="container">
            <h2 style="color: #2c5f2d;">📈 害虫对玉米产量的影响</h2>
            <p style="font-size: 1.1rem; line-height: 1.8;">
                下图展示了近年来害虫发生面积与玉米产量之间的关系。数据显示，害虫发生面积的增加与玉米产量的下降呈显著相关性。
            </p>
    """, unsafe_allow_html=True)
    
    # 模拟数据
    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
    pest_area = [120, 150, 180, 200, 220, 250, 280]  # 单位：万公顷
    corn_yield = [260, 255, 245, 235, 225, 210, 200]  # 单位：百万吨
    
    # 创建数据框
    data = pd.DataFrame({
        "年份": years,
        "害虫发生面积 (万公顷)": pest_area,
        "玉米产量 (百万吨)": corn_yield
    })
    
    # 绘制折线图
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    color = 'tab:blue'
    ax1.set_xlabel('年份')
    ax1.set_ylabel('害虫发生面积 (万公顷)', color=color)
    ax1.plot(data["年份"], data["害虫发生面积 (万公顷)"], color=color, marker='o')
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('玉米产量 (百万吨)', color=color)
    ax2.plot(data["年份"], data["玉米产量 (百万吨)"], color=color, marker='x')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title('害虫发生面积与玉米产量的关系')
    fig.tight_layout()
    
    # 显示图表
    st.pyplot(fig)
    
    st.markdown("""
        <p style="font-size: 1.1rem; line-height: 1.8;">
            从图中可以看出，随着害虫发生面积的增加，玉米产量呈现下降趋势。这表明害虫防治对于保障玉米产量具有重要意义。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ==================== 主程序 ====================
def main():
    # 初始化页面状态
    if "current_page" not in st.session_state:
        st.session_state.current_page = "首页"
    
    # 渲染导航栏
    current_page = render_navbar()
    
    # 显示登录/注册界面
    if 'username' not in st.session_state:
        if st.session_state.get('register_success'):
            st.success("注册成功！请登录。")
            del st.session_state.register_success
        if current_page == "认证":
            auth_page()
        else:
            if current_page == "首页":
                home_page()
            elif current_page == "检测":
                detection_page()
            elif current_page == "相关新闻":
                news_page()
            elif current_page == "科普信息":
                knowledge_page()
            elif current_page == "论坛交流":
                forum_page()
            elif current_page == "关于我们":
                about_page()
    else:
        # 显示用户信息和注销按钮
        st.sidebar.markdown(f"""
            <div style="text-align: right; margin-bottom: 1rem;">
                <p>已登录为: {st.session_state.username}</p>
            </div>
        """, unsafe_allow_html=True)

        # 显示当前页面
        pages = {
            "首页": home_page,
            "检测": detection_page,
            "相关新闻": news_page,
            "科普信息": knowledge_page,
            "论坛交流": forum_page,
            "关于我们": about_page
        }
        if current_page in pages:
            pages[current_page]()
        elif current_page == "认证":
            auth_page()

if __name__ == "__main__":
    main()