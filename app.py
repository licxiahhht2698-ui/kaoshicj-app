import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu
import openai

# --- 1. 页面配置 ---
st.set_page_config(page_title="星辰学情管理与AI测评系统", layout="wide", page_icon="🏫", initial_sidebar_state="collapsed")

# ==============================================================================
# 🔐 安全配置读取 (从 secrets 中读取，代码中不再包含任何密码和链接)
# ==============================================================================
try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PWD"]
    SCORE_URL_PHYSICS = st.secrets.get("URL_SCORE_PHYSICS", "")
    SCORE_URL_HISTORY = st.secrets.get("URL_SCORE_HISTORY", "")
    
    SUBJECT_URLS = {
        "⚡ 物理": st.secrets.get("URL_DETAIL_PHYSICS", ""),
        "🧪 化学": st.secrets.get("URL_DETAIL_CHEMISTRY", ""),
        "🧬 生物": st.secrets.get("URL_DETAIL_BIOLOGY", ""),
        "📜 历史": st.secrets.get("URL_DETAIL_HISTORY", ""),
        "🌍 地理": st.secrets.get("URL_DETAIL_GEOGRAPHY", ""),
        "⚖️ 政治": st.secrets.get("URL_DETAIL_POLITICS", ""),
        "📐 数学": st.secrets.get("URL_DETAIL_MATH", ""),
        "📖 语文": st.secrets.get("URL_DETAIL_CHINESE", ""),
        "🔤 英语": st.secrets.get("URL_DETAIL_ENGLISH", "")
    }
    
    # 获取 AI API KEY
    AI_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
except Exception as e:
    st.error("⚠️ 系统配置读取失败，请检查 .streamlit/secrets.toml 文件是否配置正确。")
    st.stop()

# --- 初始化 AI 客户端 ---
if AI_API_KEY:
    # 此处默认使用 DeepSeek 的接口，如果您用 Kimi 或智谱，只需修改 base_url
    client = openai.OpenAI(api_key=AI_API_KEY, base_url="https://api.deepseek.com")
else:
    client = None

# ==============================================================================
# 🧠 AI 导师功能定义
# ==============================================================================
def get_ai_advice_for_student(student_name, subject, weak_points, strong_points):
    if not client: return "⚠️ AI 尚未配置，无法生成建议。"
    prompt = f"""
    你是一位拥有20年教学经验的高中{subject}金牌教师。
    你的学生 {student_name} 刚完成了一次考试分析。
    他的优势知识点是：{strong_points}。
    他的薄弱知识点是：{weak_points}。
    请你用温暖、鼓励、专业的语气，直接对他说话，给他写一段大约300字的个性化学习建议和下一步的提分计划。
    不要说空话，给出具体的学习步骤建议。
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的教育AI导师。"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 生成失败，请稍后再试或检查网络/额度。错误信息：{e}"

def get_ai_advice_for_teacher(subject, weak_points_list):
    if not client: return "⚠️ AI 尚未配置，无法生成建议。"
    prompt = f"""
    你是一位高中教研员。你们学校高三年级刚考完{subject}。
    全校大数据显示，学生们失分最严重的共性薄弱点是：{weak_points_list}。
    请你给{subject}备课组的老师们写一份大约300字的“讲评课教研建议”，指出针对这些薄弱点，课堂上该采用什么教学策略来帮助学生突破。
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的学校教研组长AI。"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 生成失败: {e}"

# ==============================================================================
# --- 初始化状态与 CSS ---
# ==============================================================================
if 'logged_in_student' not in st.session_state: st.session_state.logged_in_student = None
if 'logged_in_direction' not in st.session_state: st.session_state.logged_in_direction = None
if 'is_admin' not in st.session_state: st.session_state.is_admin = False

def logout():
    st.session_state.logged_in_student = None
    st.session_state.logged_in_direction = None
    st.session_state.is_admin = False
    st.rerun()

st.markdown("""
<style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
    .stApp { background-color: #f4f7f9; }
    div[data-testid="stMetric"] { background-color: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.03); border: 1px solid #ebeef5; text-align: center; transition: transform 0.2s; }
    div[data-testid="stMetric"]:hover { transform: translateY(-3px); box-shadow: 0 6px 15px rgba(0,0,0,0.08); }
    div[data-testid="stForm"] { background-color: #ffffff; padding: 30px; border-radius: 15px; box-shadow: 0 8px 20px rgba(0,0,0,0.05); border: none; }
    div[data-testid="stFormSubmitButton"] > button { background-color: #0068C9; color: white; font-weight: bold; border-radius: 8px; border: none; padding: 10px 0; }
    div[data-testid="stFormSubmitButton"] > button:hover { background-color: #0052a3; box-shadow: 0 4px 12px rgba(0, 104, 201, 0.3); }
    .ai-box { background: linear-gradient(135deg, #f0f7ff 0%, #e6f3ff 100%); border-left: 5px solid #0068C9; padding: 20px; border-radius: 8px; font-size: 15px; line-height: 1.6; color: #333;}
</style>
""", unsafe_allow_html=True)

# --- 顶端导航 ---
selected_nav = option_menu(
    menu_title=None, options=["成绩总览", "深度诊断", "教师后台"], 
    icons=["clipboard-data", "bullseye", "person-badge"], menu_icon="cast", default_index=0, orientation="horizontal",
    styles={
        "container": {"padding": "5px", "background-color": "#ffffff", "border-radius": "12px", "box-shadow": "0 4px 15px rgba(0,0,0,0.08)", "margin-bottom": "30px", "position": "sticky", "top": "15px", "z-index": "9999"},
        "icon": {"color": "#888", "font-size": "18px"}, 
        "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "border-radius": "8px", "color": "#555", "font-weight": "600"},
        "nav-link-selected": {"background-color": "#0068C9", "color": "white", "font-weight": "bold"},
    }
)

@st.cache_data(ttl=600)
def load_data(url, header_lines=0):
    try: return pd.read_csv(url, header=header_lines, on_bad_lines='skip')
    except: return None

# ==============================================================================
# 🚀 页面 1 & 2: 学生端
# ==============================================================================
if selected_nav in ["成绩总览", "深度诊断"]:
    
    if not st.session_state.logged_in_student:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("<br><h2 style='text-align: center; color: #333;'>👨‍🎓 欢迎登录系统</h2><br>", unsafe_allow_html=True)
            with st.form("student_login"):
                direction = st.selectbox("📝 选择方向", ["物理方向", "历史方向"])
                name = st.text_input("👤 学生姓名", placeholder="请输入真实姓名")
                stu_id = st.text_input("🔢 考号/学号", placeholder="请输入准确考号")
                if st.form_submit_button("🔍 立即查询", use_container_width=True):
                    if name and stu_id:
                        st.session_state.logged_in_student = name.strip()
                        st.session_state.logged_in_id = stu_id.strip()
                        st.session_state.logged_in_direction = direction
                        st.rerun()
                    else: st.error("⚠️ 请完整填写姓名和考号")
    
    else:
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"**当前用户：** {st.session_state.logged_in_student} | **方向：** {st.session_state.logged_in_direction}")
        with c2:
            if st.button("🚪 退出登录", use_container_width=True): logout()
        st.divider()

        target_url = SCORE_URL_PHYSICS if st.session_state.logged_in_direction == "物理方向" else SCORE_URL_HISTORY
        
        # --- 页面1: 成绩总览 ---
        if selected_nav == "成绩总览":
            df = load_data(target_url)
            if df is not None:
                id_col = '考号' if '考号' in df.columns else '学号'
                df[id_col] = df[id_col].astype(str).str.strip()
                student = df[(df['姓名'].astype(str).str.strip() == st.session_state.logged_in_student) & (df[id_col] == st.session_state.logged_in_id)]
                
                if len(student) == 0: st.error("❌ 未匹配到您的成绩信息。")
                else:
                    stu_data = student.iloc[0]
                    st.markdown("### 🏆 本次考试概览")
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("姓名", stu_data['姓名'])
                    k2.metric("方向", st.session_state.logged_in_direction)
                    
                    if '总分' in stu_data: total = stu_data['总分']
                    else:
                        exclude = ['姓名', '考号', '学号', '班级', '排名', '总分', '班级排名', '年级排名']
                        cols = [c for c in df.columns if c not in exclude and pd.to_numeric(stu_data[c], errors='coerce') >= 0]
                        total = sum([stu_data[c] for c in cols])
                        
                    k3.metric("考试总分", f"{total}")
                    k4.metric("班级排名", stu_data.get('班级排名', 'N/A'))
                    
                    st.markdown("<br>### 📊 各科得分对比", unsafe_allow_html=True)
                    exclude_cols = ['姓名', '考号', '学号', '班级', '总分', '班级排名', '年级排名', 'Unnamed', '序号']
                    subject_cols = [c for c in df.columns if c not in exclude_cols and not str(c).startswith('Unnamed') and pd.to_numeric(stu_data[c], errors='coerce') >= 0]
                    
                    if subject_cols:
                        chart_data = pd.DataFrame({"科目": subject_cols, "得分": [stu_data[c] for c in subject_cols]})
                        col_bar, col_radar = st.columns(2)
                        with col_bar:
                            fig1 = px.bar(chart_data, x='科目', y='得分', text_auto=True, color='科目')
                            fig1.update_layout(showlegend=False, margin=dict(t=40, b=20, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig1, use_container_width=True)
                        with col_radar:
                            fig2 = px.line_polar(chart_data, r='得分', theta='科目', line_close=True)
                            fig2.update_traces(fill='toself', line_color='#0068C9')
                            fig2.update_layout(margin=dict(t=40, b=20, l=40, r=40), paper_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig2, use_container_width=True)
            else: st.warning("总成绩数据未准备好。")
                
        # --- 页面2: 深度诊断 + AI导师 ---
        elif selected_nav == "深度诊断":
            st.markdown("### 🎯 学科知识点深度剖析")
            avail_subs = {k: v for k, v in SUBJECT_URLS.items() if v and v.strip()}
            if not avail_subs: st.info("老师暂时还未配置单科诊断数据源。")
            else:
                sel_sub = st.selectbox("👇 请选择需要查阅的科目报告", list(avail_subs.keys()))
                df_diag = load_data(avail_subs[sel_sub], header_lines=[0, 1, 2])
                
                if df_diag is not None:
                    name_idx, id_idx = -1, -1
                    for i, col in enumerate(df_diag.columns):
                        if '姓名' in str(col[0]): name_idx = i
                        if '考号' in str(col[0]) or '学号' in str(col[0]): id_idx = i
                    
                    all_names = df_diag.iloc[:, name_idx].astype(str).str.strip().values
                    all_ids = df_diag.iloc[:, id_idx].astype(str).str.strip().values
                    
                    found_idx = -1
                    for idx, (n, i) in enumerate(zip(all_names, all_ids)):
                        if n == st.session_state.logged_in_student and i == st.session_state.logged_in_id:
                            found_idx = idx; break
                    
                    if found_idx == -1: st.warning(f"在 {sel_sub} 中未找到您的试卷数据。")
                    else:
                        knowledge_map = {} 
                        for col in df_diag.columns:
                            q_name, k_point = str(col[0]).strip(), str(col[1]).strip()
                            try: full = float(col[2])
                            except: full = 0
                            if '姓名' in q_name or '考号' in q_name or full <= 0: continue
                            if k_point not in knowledge_map: knowledge_map[k_point] = {'my': 0, 'full': 0, 'class_total': 0}
                            try: my_s = float(df_diag.iloc[found_idx][col])
                            except: my_s = 0
                            class_s = pd.to_numeric(df_diag[col], errors='coerce').mean()
                            knowledge_map[k_point]['my'] += my_s
                            knowledge_map[k_point]['full'] += full
                            knowledge_map[k_point]['class_total'] += class_s
                        
                        k_data = []
                        weak_points_list = []
                        strong_points_list = []
                        
                        for kp, val in knowledge_map.items():
                            my_rate = round((val['my']/val['full'])*100, 1) if val['full']>0 else 0
                            avg_rate = round((val['class_total']/val['full'])*100, 1) if val['full']>0 else 0
                            k_data.append({'知识点': kp, '我的掌握率': my_rate, '班级平均': avg_rate})
                            if my_rate < avg_rate: weak_points_list.append(kp)
                            else: strong_points_list.append(kp)
                        
                        df_kp = pd.DataFrame(k_data)
                        if not df_kp.empty:
                            c_chart, c_text = st.columns([1.2, 1])
                            with c_chart:
                                fig = go.Figure()
                                cats = df_kp['知识点'].tolist() + [df_kp['知识点'].tolist()[0]]
                                mys = df_kp['我的掌握率'].tolist() + [df_kp['我的掌握率'].tolist()[0]]
                                avgs = df_kp['班级平均'].tolist() + [df_kp['班级平均'].tolist()[0]]
                                fig.add_trace(go.Scatterpolar(r=avgs, theta=cats, fill='toself', name='班级平均', line_color='#cccccc'))
                                fig.add_trace(go.Scatterpolar(r=mys, theta=cats, fill='toself', name='我的掌握', line_color='#FF4B4B'))
                                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20))
                                st.plotly_chart(fig, use_container_width=True)
                            with c_text:
                                st.markdown("#### 🩺 专家系统诊断建议")
                                if weak_points_list:
                                    st.error("🚨 **以下知识模块出现明显丢分，需针对性突破：**")
                                    for row in k_data:
                                        if row['知识点'] in weak_points_list:
                                            diff = row['班级平均'] - row['我的掌握率']
                                            st.write(f"▪ **{row['知识点']}** (落后平均 {diff:.1f}%)")
                                else:
                                    st.success("🎉 **太棒了！** 您在该科目的所有考核知识点均达到或超过班级平均水平！")
                            
                            # === 🤖 接入 AI 导师分析 ===
                            st.divider()
                            st.markdown("### 🤖 AI 专属导师提分计划")
                            if AI_API_KEY:
                                if st.button(f"✨ 一键生成 {sel_sub} 个性化提分建议", type="primary"):
                                    with st.spinner("AI 导师正在为您深度分析试卷，定制专属学习计划..."):
                                        weak_str = "、".join(weak_points_list) if weak_points_list else "无明显薄弱点"
                                        strong_str = "、".join(strong_points_list) if strong_points_list else "基础待整体加强"
                                        
                                        ai_reply = get_ai_advice_for_student(st.session_state.logged_in_student, sel_sub, weak_str, strong_str)
                                        st.markdown(f"<div class='ai-box'><b>AI导师：</b><br><br>{ai_reply}</div>", unsafe_allow_html=True)
                            else:
                                st.info("💡 提示：管理员尚未配置 AI 密钥，暂无法启用 AI 导师功能。")

# ==============================================================================
# 🚀 页面 3: 教师后台 (管理员模式)
# ==============================================================================
elif selected_nav == "教师后台":
    
    if not st.session_state.is_admin:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("<br><h2 style='text-align: center; color: #333;'>👨‍🏫 教务管理中枢</h2><br>", unsafe_allow_html=True)
            with st.form("admin_login"):
                pwd = st.text_input("🔐 管理员密码", type="password")
                if st.form_submit_button("验证进入", use_container_width=True):
                    if pwd == ADMIN_PASSWORD:
                        st.session_state.is_admin = True
                        st.rerun()
                    else: st.error("密码错误。")
    
    else:
        c1, c2 = st.columns([5, 1])
        c1.markdown("### ⚙️ 管理员控制台")
        if c2.button("退出后台", use_container_width=True): logout()
        
        adm_menu = st.radio("系统功能：", ["🏆 班级成绩PK", "📈 学情总览", "🧠 共性诊断与 AI 教研"], horizontal=True)
        st.divider()
        
        adm_direction = st.selectbox("分析方向", ["物理方向", "历史方向"])
        target_url = SCORE_URL_PHYSICS if adm_direction == "物理方向" else SCORE_URL_HISTORY
        
        if adm_menu == "🏆 班级成绩PK":
            df = load_data(target_url)
            if df is not None and '班级' in df.columns:
                exclude = ['姓名', '考号', '学号', '班级', '排名', '总分', '班级排名', '年级排名']
                subjects = [c for c in df.columns if c not in exclude and pd.to_numeric(df[c], errors='coerce').notna().all()]
                class_avg = df.groupby('班级')[subjects + ['总分']].mean().round(1).reset_index()
                
                c_a, c_b = st.columns(2)
                with c_a:
                    fig_total = px.bar(class_avg, x='班级', y='总分', color='班级', text_auto=True, title="各班总分均分对照")
                    fig_total.update_layout(paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_total, use_container_width=True)
                with c_b:
                    sel_sub = st.selectbox("切换单科视角", subjects)
                    fig_sub = px.bar(class_avg, x='班级', y=sel_sub, color='班级', text_auto=True, title=f"各班 {sel_sub} 均分")
                    fig_sub.update_layout(paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_sub, use_container_width=True)

        elif adm_menu == "📈 学情总览":
            df = load_data(target_url)
            if df is not None and '总分' in df.columns:
                m1, m2, m3 = st.columns(3)
                m1.metric("参考总人数", len(df))
                m2.metric("年级均分", round(df['总分'].mean(), 1))
                m3.metric("最高分", df['总分'].max())
                fig_hist = px.histogram(df, x="总分", nbins=15, title="总分正态分布情况", color_discrete_sequence=['#0068C9'])
                st.plotly_chart(fig_hist, use_container_width=True)

        elif adm_menu == "🧠 共性诊断与 AI 教研":
            avail_subs = [k for k, v in SUBJECT_URLS.items() if v]
            sel_diagnosis = st.selectbox("选择要分析的学科", avail_subs)
            if sel_diagnosis:
                df_diag = load_data(SUBJECT_URLS[sel_diagnosis], header_lines=[0, 1, 2])
                if df_diag is not None:
                    k_stats = {}
                    for col in df_diag.columns:
                        q_name, k_point = str(col[0]).strip(), str(col[1]).strip()
                        try: full = float(col[2])
                        except: full = 0
                        if full <= 0 or '姓名' in q_name: continue
                        if k_point not in k_stats: k_stats[k_point] = []
                        k_stats[k_point].append(pd.to_numeric(df_diag[col], errors='coerce').mean() / full)
                    
                    k_final = [{"知识点": kp, "年级平均掌握率": round(sum(rates)/len(rates)*100, 1)} for kp, rates in k_stats.items()]
                    df_k = pd.DataFrame(k_final).sort_values("年级平均掌握率")
                    
                    fig_k = px.bar(df_k, x="年级平均掌握率", y="知识点", orientation='h', title=f"全校【{sel_diagnosis}】薄弱点扫描", color="年级平均掌握率", color_continuous_scale='RdYlGn')
                    st.plotly_chart(fig_k, use_container_width=True)
                    
                    # === 🤖 AI 教研助手 ===
                    if AI_API_KEY:
                        st.divider()
                        st.markdown("### 🤖 AI 教研建议")
                        if st.button("✨ 一键生成教研组讲评建议", type="primary"):
                            with st.spinner("AI 正在分析全级数据并编写教研报告..."):
                                # 选出最差的3个考点
                                worst_points = "、".join(df_k.head(3)['知识点'].tolist())
                                ai_teacher_reply = get_ai_advice_for_teacher(sel_diagnosis, worst_points)
                                st.markdown(f"<div class='ai-box'><b>教研专家AI：</b><br><br>{ai_teacher_reply}</div>", unsafe_allow_html=True)
