import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu
import openai
import os

# ==============================================================================
# 1. 页面基础配置 
# ==============================================================================
st.set_page_config(page_title="英华学校高中部考试学情智能分析", layout="wide", page_icon="🏫", initial_sidebar_state="collapsed")

# ==============================================================================
# 🔐 安全配置读取
# ==============================================================================
try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PWD"]
    # 智能兼容：如果您在 Secrets 里配了 TEACHER_PWD 就用它，没配就和管理员密码一样
    TEACHER_PASSWORD = st.secrets.get("TEACHER_PWD", ADMIN_PASSWORD) 
    
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
    
    AI_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
except Exception as e:
    st.error("⚠️ 系统配置读取失败，请检查 Streamlit 后台的 Secrets 是否配置正确。")
    st.stop()

if AI_API_KEY:
    client = openai.OpenAI(api_key=AI_API_KEY, base_url="https://api.deepseek.com")
else:
    client = None

# ==============================================================================
# 🛠️ 核心数据加载与动态光荣榜计算
# ==============================================================================
@st.cache_data(ttl=600)
def load_data(url, header_lines=0):
    if not url or not url.strip(): return None
    try: return pd.read_csv(url, header=header_lines, on_bad_lines='skip')
    except: return None

def get_dynamic_top5_banner():
    str_p = ""
    str_h = ""
    try:
        if SCORE_URL_PHYSICS:
            df_p = load_data(SCORE_URL_PHYSICS)
            if df_p is not None and '总分' in df_p.columns and '姓名' in df_p.columns:
                df_p['总分'] = pd.to_numeric(df_p['总分'], errors='coerce')
                top_p = df_p.dropna(subset=['总分']).sort_values(by='总分', ascending=False).head(5)['姓名'].astype(str).str.strip().tolist()
                if top_p: str_p = f"🚀 理科前五：{'、'.join(top_p)}"
                
        if SCORE_URL_HISTORY:
            df_h = load_data(SCORE_URL_HISTORY)
            if df_h is not None and '总分' in df_h.columns and '姓名' in df_h.columns:
                df_h['总分'] = pd.to_numeric(df_h['总分'], errors='coerce')
                top_h = df_h.dropna(subset=['总分']).sort_values(by='总分', ascending=False).head(5)['姓名'].astype(str).str.strip().tolist()
                if top_h: str_h = f"🌟 文科前五：{'、'.join(top_h)}"
                
        if str_p or str_h:
            banner_html = "🎉 <b>成绩表彰光荣榜</b> 🏆<br>"
            if str_p: banner_html += f"<span style='font-size: 16px; color: #D97706;'>{str_p}</span>"
            if str_p and str_h: banner_html += "<br>"
            if str_h: banner_html += f"<span style='font-size: 16px; color: #D97706;'>{str_h}</span>"
            return banner_html
        else:
            return "🎉 欢迎使用英华学校高中部考试学情智能分析系统！ 🏆"
    except Exception as e:
        return "🎉 欢迎使用英华学校高中部考试学情智能分析系统！ 🏆"

# ==============================================================================
# 🧠 AI 导师功能定义 (30天缓存)
# ==============================================================================
@st.cache_data(ttl=2592000, show_spinner=False)
def get_ai_advice_for_student(student_name, subject, weak_points, strong_points):
    if not client: return "⚠️ AI 尚未配置，无法生成建议。"
    prompt = f"你是拥有20年经验的高中{subject}教师。学生 {student_name} 优势：{strong_points}。薄弱：{weak_points}。请写约300字的个性化鼓励和提分计划。"
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": "你是专业AI导师。"}, {"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"AI 生成失败: {e}"

@st.cache_data(ttl=2592000, show_spinner=False)
def get_ai_advice_for_teacher(subject, weak_points_list):
    if not client: return "⚠️ AI 尚未配置。"
    prompt = f"你是教研员。高三年级{subject}失分严重的共性薄弱点是：{weak_points_list}。请给老师们写约300字的讲评课教研建议。"
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": "你是教研专家AI。"}, {"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"AI 生成失败: {e}"

# ==============================================================================
# --- 状态与样式 ---
# ==============================================================================
if 'logged_in_student' not in st.session_state: st.session_state.logged_in_student = None
if 'logged_in_direction' not in st.session_state: st.session_state.logged_in_direction = None
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'is_teacher' not in st.session_state: st.session_state.is_teacher = False
if 'teacher_subject' not in st.session_state: st.session_state.teacher_subject = None

def logout():
    st.session_state.logged_in_student = None
    st.session_state.logged_in_direction = None
    st.session_state.is_admin = False
    st.session_state.is_teacher = False
    st.session_state.teacher_subject = None
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
    .congrats-banner {
        background: linear-gradient(90deg, #FFFBEB, #FFF7ED);
        border: 2px solid #FCD34D;
        color: #92400E;
        padding: 12px 20px;
        border-radius: 12px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        margin-top: 0px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(252, 211, 77, 0.2);
        line-height: 1.6;
    }
    .main-title { text-align: center; color: #1E3A8A; font-size: 28px; font-weight: 800; margin-bottom: 15px; }
    .ai-box { background: linear-gradient(135deg, #f0f7ff 0%, #e6f3ff 100%); border-left: 5px solid #0068C9; padding: 20px; border-radius: 8px; font-size: 15px; color: #333;}
</style>
""", unsafe_allow_html=True)

selected_nav = option_menu(
    menu_title=None, options=["成绩总览", "深度诊断", "教师后台"], 
    icons=["clipboard-data", "bullseye", "person-badge"], menu_icon="cast", default_index=0, orientation="horizontal",
    styles={
        "container": {"padding": "5px", "background-color": "#ffffff", "border-radius": "12px", "box-shadow": "0 4px 15px rgba(0,0,0,0.08)", "margin-bottom": "30px", "position": "sticky", "top": "15px", "z-index": "9999"},
        "nav-link-selected": {"background-color": "#0068C9", "color": "white", "font-weight": "bold"},
    }
)

# ==============================================================================
# 🚀 页面逻辑
# ==============================================================================
if selected_nav in ["成绩总览", "深度诊断"]:
    
    if not st.session_state.logged_in_student:
        st.markdown("<h1 class='main-title'>🏫 英华学校高中部考试学情智能分析系统</h1>", unsafe_allow_html=True)
        banner_text = get_dynamic_top5_banner()
        st.markdown(f'<div class="congrats-banner">{banner_text}</div>', unsafe_allow_html=True)
        
        col_left, col_mid, col_right = st.columns([1, 1.8, 1])
        with col_left:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if os.path.exists("panda.gif"): st.image("panda.gif", use_container_width=True)
        with col_mid:
            with st.form("student_login"):
                st.markdown("<h3 style='text-align: center; color: #555;'>👨‍🎓 学生/家长登录入口</h3><br>", unsafe_allow_html=True)
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
        with col_right:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if os.path.exists("star.gif"): st.image("star.gif", use_container_width=True)
    
    else:
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"**当前用户：** {st.session_state.logged_in_student} | **方向：** {st.session_state.logged_in_direction}")
        if c2.button("🚪 退出登录", use_container_width=True): logout()
        st.divider()

        target_url = SCORE_URL_PHYSICS if st.session_state.logged_in_direction == "物理方向" else SCORE_URL_HISTORY
        
        if selected_nav == "成绩总览":
            df = load_data(target_url)
            if df is not None:
                id_col = '考号' if '考号' in df.columns else '学号'
                df[id_col] = df[id_col].astype(str).str.strip()
                student = df[(df['姓名'].astype(str).str.strip() == st.session_state.logged_in_student) & (df[id_col] == st.session_state.logged_in_id)]
                
                if len(student) == 0: st.error("❌ 未匹配到成绩。请确认考号和方向。")
                else:
                    stu_data = student.iloc[0]
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("姓名", stu_data['姓名'])
                    k2.metric("方向", st.session_state.logged_in_direction)
                    total = stu_data.get('总分', 0)
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
            else: st.warning("数据未准备好。")
                
        elif selected_nav == "深度诊断":
            avail_subs = {k: v for k, v in SUBJECT_URLS.items() if v and v.strip()}
            if not avail_subs: st.info("暂未配置单科诊断数据。")
            else:
                sel_sub = st.selectbox("👇 选择科目报告", list(avail_subs.keys()))
                df_diag = load_data(avail_subs[sel_sub], header_lines=[0, 1, 2])
                if df_diag is not None:
                    name_idx, id_idx = -1, -1
                    for i, col in enumerate(df_diag.columns):
                        if '姓名' in str(col[0]): name_idx = i
                        if '考号' in str(col[0]) or '学号' in str(col[0]): id_idx = i
                    if name_idx != -1 and id_idx != -1:
                        all_names = df_diag.iloc[:, name_idx].astype(str).str.strip().values
                        all_ids = df_diag.iloc[:, id_idx].astype(str).str.strip().values
                        found_idx = -1
                        for idx, (n, i) in enumerate(zip(all_names, all_ids)):
                            if n == st.session_state.logged_in_student and i == st.session_state.logged_in_id: found_idx = idx; break
                        if found_idx == -1: st.warning("未查到该科数据。")
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
                            
                            k_data, weak_points_list, strong_points_list = [], [], []
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
                                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor='rgba(0,0,0,0)')
                                    st.plotly_chart(fig, use_container_width=True)
                                with c_text:
                                    st.markdown("#### 🩺 专家系统诊断")
                                    if weak_points_list:
                                        for row in k_data:
                                            if row['知识点'] in weak_points_list:
                                                st.write(f"▪ **{row['知识点']}** (落后 {row['班级平均'] - row['我的掌握率']:.1f}%)")
                                    else: st.success("🎉 所有知识点均达标！")
                                
                                st.divider()
                                if AI_API_KEY:
                                    if st.button(f"✨ 提取专家 AI 提分建议", type="primary"):
                                        with st.spinner("AI 导师正在云端调取档案..."):
                                            w_str = "、".join(weak_points_list) if weak_points_list else "无"
                                            s_str = "、".join(strong_points_list) if strong_points_list else "无"
                                            ai_reply = get_ai_advice_for_student(st.session_state.logged_in_student, sel_sub, w_str, s_str)
                                            st.markdown(f"<div class='ai-box'><b>AI导师：</b><br><br>{ai_reply}</div>", unsafe_allow_html=True)

# ==============================================================================
# 🚀 页面 3: 教师后台 (包含超级管理 & 次级单科管理)
# ==============================================================================
elif selected_nav == "教师后台":
    
    # --- 1. 未登录状态下的登录界面 ---
    if not st.session_state.is_admin and not st.session_state.is_teacher:
        st.markdown("<h1 class='main-title'>🏫 英华学校高中部考试学情智能分析系统</h1>", unsafe_allow_html=True)
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True) 
        
        col_left, col_mid, col_right = st.columns([1, 1.8, 1])
        with col_left:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if os.path.exists("panda.gif"): st.image("panda.gif", use_container_width=True)
        with col_mid:
            with st.form("admin_login"):
                st.markdown("<h3 style='text-align: center; color: #555;'>👨‍🏫 教务管理中枢</h3><br>", unsafe_allow_html=True)
                
                # 动态选择身份
                role = st.radio("请选择您的登录身份：", ["👨‍🏫 学科教师 (仅看本学科)", "👑 教务处/年级长 (全科全览)"], horizontal=True)
                sel_sub = None
                if "学科教师" in role:
                    sel_sub = st.selectbox("📝 选择您任教的学科：", list(SUBJECT_URLS.keys()))
                
                pwd = st.text_input("🔐 管理密码", type="password")
                
                if st.form_submit_button("验证进入", use_container_width=True):
                    # 如果选了教务处，必须输入ADMIN密码；如果选了学科教师，兼容两种密码
                    if ("教务处" in role and pwd == ADMIN_PASSWORD) or ("学科教师" in role and (pwd == TEACHER_PASSWORD or pwd == ADMIN_PASSWORD)):
                        if "教务处" in role:
                            st.session_state.is_admin = True
                        else:
                            st.session_state.is_teacher = True
                            st.session_state.teacher_subject = sel_sub
                        st.rerun()
                    else: 
                        st.error("密码错误，请重试。")
        with col_right:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if os.path.exists("star.gif"): st.image("star.gif", use_container_width=True)
            
    # --- 2. 教务处超级管理界面 ---
    elif st.session_state.is_admin:
        c1, c2 = st.columns([5, 1])
        c1.markdown("### 👑 教务处全局控制台 (全科权限)")
        if c2.button("退出后台", use_container_width=True): logout()
        adm_menu = st.radio("功能：", ["🏆 班级成绩PK", "📈 学情总览", "🧠 AI教研"], horizontal=True)
        adm_direction = st.selectbox("方向", ["物理方向", "历史方向"])
        target_url = SCORE_URL_PHYSICS if adm_direction == "物理方向" else SCORE_URL_HISTORY
        
        if adm_menu == "🏆 班级成绩PK":
            df = load_data(target_url)
            if df is not None and '班级' in df.columns:
                exclude = ['姓名', '考号', '学号', '班级', '排名', '总分', '班级排名', '年级排名']
                subjects = [c for c in df.columns if c not in exclude and pd.to_numeric(df[c], errors='coerce').notna().all()]
                class_avg = df.groupby('班级')[subjects + ['总分']].mean().round(1).reset_index()
                c_a, c_b = st.columns(2)
                with c_a: st.plotly_chart(px.bar(class_avg, x='班级', y='总分', color='班级', text_auto=True), use_container_width=True)
                with c_b:
                    sel_sub = st.selectbox("单科视角", subjects)
                    st.plotly_chart(px.bar(class_avg, x='班级', y=sel_sub, color='班级', text_auto=True), use_container_width=True)

        elif adm_menu == "📈 学情总览":
            df = load_data(target_url)
            if df is not None and '总分' in df.columns:
                st.plotly_chart(px.histogram(df, x="总分", nbins=15), use_container_width=True)

        elif adm_menu == "🧠 AI教研":
            avail_subs = [k for k, v in SUBJECT_URLS.items() if v and v.strip()]
            sel_diagnosis = st.selectbox("选择学科", avail_subs) if avail_subs else None
            if sel_diagnosis:
                df_diag = load_data(SUBJECT_URLS[sel_diagnosis], header_lines=[0, 1, 2])
                if df_diag is not None:
                    k_stats = {}
                    for col in df_diag.columns:
                        try: full = float(col[2])
                        except: full = 0
                        if full > 0 and '姓名' not in str(col[0]):
                            kp = str(col[1]).strip()
                            if kp not in k_stats: k_stats[kp] = []
                            k_stats[kp].append(pd.to_numeric(df_diag[col], errors='coerce').mean() / full)
                    if k_stats:
                        k_final = [{"知识点": kp, "掌握率": round(sum(rates)/len(rates)*100, 1)} for kp, rates in k_stats.items()]
                        df_k = pd.DataFrame(k_final).sort_values("掌握率")
                        st.plotly_chart(px.bar(df_k, x="掌握率", y="知识点", orientation='h'), use_container_width=True)
                        if AI_API_KEY and st.button("✨ 提取专家 AI 教研建议", type="primary"):
                            with st.spinner("AI 正在云端调取报告..."):
                                st.markdown(f"<div class='ai-box'>{get_ai_advice_for_teacher(sel_diagnosis, '、'.join(df_k.head(3)['知识点'].tolist()))}</div>", unsafe_allow_html=True)

    # --- 3. 学科教师单科隔离界面 ---
    elif st.session_state.is_teacher:
        current_sub = st.session_state.teacher_subject
        # 提取学科纯文本 (例如把 "⚡ 物理" 变成 "物理")
        pure_sub_name = current_sub.split(" ")[-1] if " " in current_sub else current_sub 
        
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"### 👨‍🏫 【{current_sub}】教师专属控制台 (已开启权限隔离)")
        if c2.button("退出后台", use_container_width=True): logout()
        
        adm_menu = st.radio("专属功能：", [f"🏆 班级 {pure_sub_name} 成绩对比", f"🧠 {pure_sub_name} 共性诊断与 AI 教研"], horizontal=True)
        adm_direction = st.selectbox("方向选择", ["物理方向", "历史方向"])
        target_url = SCORE_URL_PHYSICS if adm_direction == "物理方向" else SCORE_URL_HISTORY
        
        if "成绩对比" in adm_menu:
            df = load_data(target_url)
            if df is not None:
                # 权限隔离：严格检查该学科是否存在，如果存在只计算该学科
                if pure_sub_name in df.columns and '班级' in df.columns:
                    # 过滤掉非数字数据
                    df[pure_sub_name] = pd.to_numeric(df[pure_sub_name], errors='coerce')
                    class_avg = df.groupby('班级')[pure_sub_name].mean().round(1).reset_index()
                    st.success(f"🔒 隐私保护已生效：您当前仅能查看各班级的【{pure_sub_name}】单科成绩分布，总分及其他科目已自动隐藏。")
                    st.plotly_chart(px.bar(class_avg, x='班级', y=pure_sub_name, color='班级', text_auto=True, title=f"各班【{pure_sub_name}】均分对比"), use_container_width=True)
                else:
                    st.warning(f"⚠️ 在当前的【{adm_direction}】总成绩表中，未找到【{pure_sub_name}】科目的有效数据。请切换方向试试。")
        
        elif "教研" in adm_menu:
            st.success(f"🔒 隐私保护已生效：您当前已直达【{current_sub}】题库底层数据。")
            df_diag = load_data(SUBJECT_URLS.get(current_sub, ""), header_lines=[0, 1, 2])
            if df_diag is not None:
                k_stats = {}
                for col in df_diag.columns:
                    try: full = float(col[2])
                    except: full = 0
                    if full > 0 and '姓名' not in str(col[0]):
                        kp = str(col[1]).strip()
                        if kp not in k_stats: k_stats[kp] = []
                        k_stats[kp].append(pd.to_numeric(df_diag[col], errors='coerce').mean() / full)
                if k_stats:
                    k_final = [{"知识点": kp, "掌握率": round(sum(rates)/len(rates)*100, 1)} for kp, rates in k_stats.items()]
                    df_k = pd.DataFrame(k_final).sort_values("掌握率")
                    st.plotly_chart(px.bar(df_k, x="掌握率", y="知识点", orientation='h', title=f"全年级【{pure_sub_name}】薄弱知识点扫描"), use_container_width=True)
                    if AI_API_KEY and st.button(f"✨ 提取【{pure_sub_name}】AI 教研建议", type="primary"):
                        with st.spinner("AI 正在云端调取报告..."):
                            st.markdown(f"<div class='ai-box'>{get_ai_advice_for_teacher(current_sub, '、'.join(df_k.head(3)['知识点'].tolist()))}</div>", unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ 暂未获取到【{current_sub}】的单科诊断表格。")
