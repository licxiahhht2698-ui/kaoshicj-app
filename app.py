import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- 1. 页面配置 ---
st.set_page_config(page_title="学情诊断与管理系统 (旗舰版)", layout="wide", page_icon="🎓")

# ==============================================================================
# ⚙️ 【配置区域】(请修改这里的链接和密码)
# ==============================================================================

# 🔑 管理员密码 (⚠️请修改)
ADMIN_PASSWORD = "123321"

# 1. 总成绩表 (用于查总分、班级PK)
SCORE_URL_PHYSICS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRyhhA4C2A9hp-2165uyRgqheKfCccT5NN0dp_FOW2Jl8FE4VmAMPajsWKiTEOCcqIxhIDnuIUwOoQ0/pub?gid=0&single=true&output=csv"  # 👈 物理方向总分链接
SCORE_URL_HISTORY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRyhhA4C2A9hp-2165uyRgqheKfCccT5NN0dp_FOW2Jl8FE4VmAMPajsWKiTEOCcqIxhIDnuIUwOoQ0/pub?gid=1671669597&single=true&output=csv"  # 👈 历史方向总分链接

# 2. 各科深度诊断表 (用于知识点分析)
SUBJECT_URLS = {
    # --- 理科 ---
    "⚡ 物理诊断": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLNvn1FqBT1F5w1J7ENAUA3YQuOvfLoohdW4ihjsEZkC_R8JZMCQPqtthzzitC2ZU3mvOMRUmo5omH/pub?gid=761604232&single=true&output=csv", 
    "🧪 化学诊断": "",
    "🧬 生物诊断": "",
    # --- 文科 ---
    "📜 历史诊断": "",
    "🌍 地理诊断": "",
    "⚖️ 政治诊断": "",
    # --- 主科 ---
    "📐 数学诊断": "https://docs.google.com/spreadsheets/d/...", # 👈 记得填这里
    "📖 语文诊断": "https://docs.google.com/spreadsheets/d/...", # 👈 记得填这里
    "🔤 英语诊断": ""
}

# ==============================================================================

# --- CSS 美化 ---
st.markdown("""
<style>
    .metric-card { background-color: #f8f9fa; border-left: 5px solid #1f77b4; padding: 15px; margin-bottom: 10px; border-radius: 5px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #fff; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏逻辑 ---
with st.sidebar:
    st.title("🎓 系统导航")
    
    # 1. 方向选择
    direction = st.selectbox("请选择分科方向", ["物理方向", "历史方向"])
    st.divider()

    # 2. 身份切换 (学生 vs 管理员)
    mode = st.radio("身份选择", ["👨‍🎓 学生/家长查询", "👨‍🏫 管理者入口"])
    
    if mode == "👨‍🎓 学生/家长查询":
        # 学生菜单
        available_menus = ["📑 成绩查询 (总分)"]
        for name, url in SUBJECT_URLS.items():
            if url and url.strip():
                available_menus.append(name)
        menu = st.radio("功能选择", available_menus)
        
        st.divider()
        st.markdown("### 🔐 学生验证")
        input_name = st.text_input("学生姓名")
        input_id = st.text_input("考号/学号")
        is_admin = False
        
    else:
        # 管理员菜单
        st.divider()
        st.markdown("### 🔐 管理员登录")
        pwd = st.text_input("请输入密码", type="password")
        
        if pwd == ADMIN_PASSWORD:
            st.success("✅ 身份验证通过")
            is_admin = True
            # 管理员专属菜单
            menu = st.radio("管理面板", ["📊 班级成绩PK", "📈 总体学情概览", "🔍 知识点共性诊断"])
        else:
            if pwd:
                st.error("❌ 密码错误")
            is_admin = False
            menu = None

# --- 函数区 ---

# 1. 通用数据加载
def load_data(url, header_lines=0):
    try:
        return pd.read_csv(url, header=header_lines, on_bad_lines='skip')
    except:
        return None

# 2. 核心功能：绘制单科雷达图 (保留完整功能)
def render_subject_analysis(subject_name, url, student_name, student_id):
    st.header(f"{subject_name} - 深度学情报告")
    try:
        df = pd.read_csv(url, header=[0, 1, 2], on_bad_lines='skip')
        
        # 自动定位列
        name_idx, id_idx = -1, -1
        for i, col in enumerate(df.columns):
            if '姓名' in str(col[0]): name_idx = i
            if '考号' in str(col[0]) or '学号' in str(col[0]): id_idx = i
            
        if name_idx == -1 or id_idx == -1:
            st.error("Excel格式错误：未找到姓名或考号列。")
            return

        all_names = df.iloc[:, name_idx].astype(str).str.strip().values
        all_ids = df.iloc[:, id_idx].astype(str).str.strip().values
        
        found_idx = -1
        for idx, (n, i) in enumerate(zip(all_names, all_ids)):
            if n == student_name.strip() and i == student_id.strip():
                found_idx = idx
                break
        
        if found_idx == -1:
            st.warning(f"未找到 {student_name} 的数据，可能是缺考或未录入。")
            return

        st.success(f"✅ 数据加载成功")
        
        knowledge_map = {} 
        for col in df.columns:
            q_name, k_point = str(col[0]).strip(), str(col[1]).strip()
            try: full = float(col[2])
            except: full = 0
            
            if '姓名' in q_name or '考号' in q_name or full <= 0: continue
            
            if k_point not in knowledge_map:
                knowledge_map[k_point] = {'my': 0, 'full': 0, 'class_total': 0}
            
            try: my_s = float(df.iloc[found_idx][col])
            except: my_s = 0
            
            class_s = pd.to_numeric(df[col], errors='coerce').mean()
            
            knowledge_map[k_point]['my'] += my_s
            knowledge_map[k_point]['full'] += full
            knowledge_map[k_point]['class_total'] += class_s
        
        k_data = []
        for kp, val in knowledge_map.items():
            k_data.append({
                '知识点': kp,
                '我的掌握率': round((val['my']/val['full'])*100, 1) if val['full']>0 else 0,
                '班级平均': round((val['class_total']/val['full'])*100, 1) if val['full']>0 else 0,
                '得分': val['my'], '满分': val['full']
            })
        
        df_kp = pd.DataFrame(k_data)
        
        if not df_kp.empty:
            c1, c2 = st.columns([1, 1])
            with c1:
                fig = go.Figure()
                cats = df_kp['知识点'].tolist() + [df_kp['知识点'].tolist()[0]]
                mys = df_kp['我的掌握率'].tolist() + [df_kp['我的掌握率'].tolist()[0]]
                avgs = df_kp['班级平均'].tolist() + [df_kp['班级平均'].tolist()[0]]
                
                fig.add_trace(go.Scatterpolar(r=avgs, theta=cats, fill='toself', name='班级平均', line_color='#cccccc'))
                fig.add_trace(go.Scatterpolar(r=mys, theta=cats, fill='toself', name='我的掌握', line_color='#1f77b4'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=350, margin=dict(t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                st.subheader("💡 诊断建议")
                weak = df_kp[df_kp['我的掌握率'] < df_kp['班级平均']]
                if not weak.empty:
                    st.error("🚨 **需重点关注的薄弱点：**")
                    for _, row in weak.iterrows():
                        st.markdown(f"- **{row['知识点']}** <br> (得分 {row['得分']}/{row['满分']} | 掌握率 {row['我的掌握率']}%)", unsafe_allow_html=True)
                else:
                    st.success("🎉 你的基础非常扎实，所有模块均超过班级平均水平！")
            
            st.divider()
            st.dataframe(df_kp, use_container_width=True)

    except Exception as e:
        st.error(f"数据读取失败: {e}")

# ==============================================================================
# 🚀 逻辑分支 A: 管理员模式 (修复版)
# ==============================================================================
if is_admin:
    st.title(f"👨‍🏫 教务管理后台 - {direction}")
    
    target_url = SCORE_URL_PHYSICS if direction == "物理方向" else SCORE_URL_HISTORY
    
    if menu == "📊 班级成绩PK":
        if not target_url:
            st.warning("暂未配置总分表链接。")
        else:
            df = load_data(target_url)
            if df is not None and '班级' in df.columns:
                st.header("🏆 班级平均分对比")
                
                # --- 【核心修复】智能识别科目列 ---
                # 排除非成绩列
                exclude = ['姓名', '考号', '学号', '班级', '排名', '总分', '班级排名', '年级排名', '序号']
                subjects = []
                
                # 遍历所有列，只要它是数字，或者虽然有空格但主要是数字，就算作科目
                for c in df.columns:
                    if c not in exclude and not c.startswith("Unnamed"):
                        # 尝试强制转数字
                        df[c] = pd.to_numeric(df[c], errors='coerce')
                        # 如果这一列里有效数字超过1个，就认为它是成绩列
                        if df[c].notna().sum() > 0:
                            subjects.append(c)

                if not subjects:
                    st.error("未检测到有效成绩列，请检查Excel数据格式。")
                else:
                    # 1. 计算各班平均分
                    # 只对 subjects 和 总分 列求平均，且自动忽略空值
                    cols_to_calc = subjects + (['总分'] if '总分' in df.columns else [])
                    class_avg = df.groupby('班级')[cols_to_calc].mean().round(1).reset_index()
                    
                    # 2. 展示总分PK图
                    if '总分' in class_avg.columns:
                        fig_total = px.bar(class_avg, x='班级', y='总分', color='班级', text_auto=True, title="各班总平均分对比")
                        st.plotly_chart(fig_total, use_container_width=True)
                    
                    # 3. 展示单科PK图
                    st.subheader("📝 单科平均分对比")
                    if subjects:
                        sel_sub = st.selectbox("选择科目查看", subjects)
                        fig_sub = px.bar(class_avg, x='班级', y=sel_sub, color='班级', text_auto=True, title=f"各班{sel_sub}平均分")
                        st.plotly_chart(fig_sub, use_container_width=True)
                    
                    with st.expander("查看详细数据表"):
                        st.dataframe(class_avg)
            else:
                st.error("读取失败或表格中缺少【班级】列，请检查Excel。")

    elif menu == "📈 总体学情概览":
        if target_url:
            df = load_data(target_url)
            if df is not None:
                # 预处理：总分列转数字
                if '总分' in df.columns:
                    df['总分'] = pd.to_numeric(df['总分'], errors='coerce')

                c1, c2, c3 = st.columns(3)
                c1.metric("参考总人数", len(df))
                
                avg_score = round(df['总分'].mean(), 1) if '总分' in df and df['总分'].notna().sum()>0 else "N/A"
                max_score = df['总分'].max() if '总分' in df and df['总分'].notna().sum()>0 else "N/A"
                
                c2.metric("年级总均分", avg_score)
                c3.metric("最高分", max_score)
                
                st.subheader("分数段分布")
                if '总分' in df and df['总分'].notna().sum() > 0:
                    fig_hist = px.histogram(df, x="总分", nbins=20, title="年级总分分布图", color_discrete_sequence=['#1f77b4'])
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("暂无总分数据")

    elif menu == "🔍 知识点共性诊断":
        st.info("此处分析所有学生的知识点掌握情况，寻找共性薄弱点。")
        avail_subs = [k for k, v in SUBJECT_URLS.items() if v]
        sel_diagnosis = st.selectbox("选择要分析的学科", avail_subs)
        
        if sel_diagnosis:
            diag_url = SUBJECT_URLS[sel_diagnosis]
            try:
                df_diag = pd.read_csv(diag_url, header=[0, 1, 2], on_bad_lines='skip')
                
                k_stats = {}
                for col in df_diag.columns:
                    q_name, k_point = str(col[0]).strip(), str(col[1]).strip()
                    try: full = float(col[2])
                    except: full = 0
                    if full <= 0 or '姓名' in q_name: continue
                    
                    if k_point not in k_stats: k_stats[k_point] = []
                    col_avg = pd.to_numeric(df_diag[col], errors='coerce').mean()
                    k_stats[k_point].append(col_avg / full)
                
                k_final = []
                for kp, rates in k_stats.items():
                    if len(rates) > 0:
                        avg_rate = sum(rates) / len(rates) * 100
                        k_final.append({"知识点": kp, "年级平均掌握率": round(avg_rate, 1)})
                
                df_k = pd.DataFrame(k_final).sort_values("年级平均掌握率")
                
                if not df_k.empty:
                    fig_k = px.bar(df_k, x="年级平均掌握率", y="知识点", orientation='h', 
                                  title=f"{sel_diagnosis} - 年级知识点掌握率排行",
                                  color="年级平均掌握率", color_continuous_scale='RdYlGn')
                    st.plotly_chart(fig_k, use_container_width=True)
                    st.error(f"🚨 年级最薄弱知识点：{df_k.iloc[0]['知识点']} (掌握率仅 {df_k.iloc[0]['年级平均掌握率']}%)")
                else:
                    st.warning("该学科暂无有效知识点数据")
            except:
                st.error("无法读取该学科数据，请检查链接。")

# ==============================================================================
# 🚀 逻辑分支 B: 学生模式
# ==============================================================================
else:
    if not input_name or not input_id:
        st.info("👈 请在左侧输入姓名和考号。")
        st.stop()
        
    if menu == "📑 成绩查询 (总分)":
        target_url = SCORE_URL_PHYSICS if direction == "物理方向" else SCORE_URL_HISTORY
        if target_url:
            try:
                df = pd.read_csv(target_url, on_bad_lines='skip')
                id_col = '考号' if '考号' in df.columns else '学号'
                if id_col not in df.columns:
                    st.error("Excel中缺少【考号】或【学号】列")
                    st.stop()

                df[id_col] = df[id_col].astype(str).str.strip()
                student = df[(df['姓名'].astype(str).str.strip() == input_name.strip()) & 
                             (df[id_col] == input_id.strip())]
                
                if len(student) == 0:
                    st.error("未找到该学生，请检查姓名考号或分科方向。")
                else:
                    stu_data = student.iloc[0]
                    c1, c2, c3 = st.columns(3)
                    c1.metric("姓名", stu_data['姓名'])
                    total = stu_data['总分'] if '总分' in stu_data else "计算中"
                    c2.metric("总分", total)
                    rank = stu_data['班级排名'] if '班级排名' in stu_data else "N/A"
                    c3.metric("班级排名", rank)
                    
                    st.divider()
                    exclude = ['姓名', '考号', '学号', '班级', '排名', '总分', '班级排名', '年级排名']
                    cols = []
                    for c in df.columns:
                         if c not in exclude and not c.startswith("Unnamed"):
                             if pd.to_numeric(stu_data[c], errors='coerce') >= 0:
                                 cols.append(c)
                    
                    if cols:
                        chart_data = pd.DataFrame({"科目": cols, "得分": [stu_data[c] for c in cols]})
                        st.plotly_chart(px.bar(chart_data, x='科目', y='得分', text_auto=True, color='科目'), use_container_width=True)
            except Exception as e:
                st.error(f"查询出错: {e}")
    else:
        target_url = SUBJECT_URLS.get(menu)
        if target_url:
            render_subject_analysis(menu, target_url, input_name, input_id)