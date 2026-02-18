import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- 1. 页面配置 ---
st.set_page_config(page_title="全校学情诊断与管理系统 (旗舰版)", layout="wide", page_icon="🏫")

# ==============================================================================
# ⚙️ 【中央配置区域】
# ==============================================================================

# 🔑 管理员密码
ADMIN_PASSWORD = "123456"

# 📚 数据仓库
SCHOOL_DATA = {
    # ==================== 高三 ====================
    "高三": {
        "2026年2月第一次月考": {
            "物理方向总分": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRyhhA4C2A9hp-2165uyRgqheKfCccT5NN0dp_FOW2Jl8FE4VmAMPajsWKiTEOCcqIxhIDnuIUwOoQ0/pub?gid=0&single=true&output=csv", 
            "历史方向总分": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRyhhA4C2A9hp-2165uyRgqheKfCccT5NN0dp_FOW2Jl8FE4VmAMPajsWKiTEOCcqIxhIDnuIUwOoQ0/pub?gid=1671669597&single=true&output=csv",
            "单科链接": {
                "⚡ 物理诊断": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLNvn1FqBT1F5w1J7ENAUA3YQuOvfLoohdW4ihjsEZkC_R8JZMCQPqtthzzitC2ZU3mvOMRUmo5omH/pub?gid=761604232&single=true&output=csv",
                "📐 数学诊断": "",
                "📖 语文诊断": "",
                "🔤 英语诊断": ""
            }
        },
        "2026年3月期中考试": {
            "物理方向总分": "", 
            "历史方向总分": "",
            "单科链接": { "⚡ 物理诊断": "" }
        }
    },
    # ==================== 高二 ====================
    "高二": {
        "2026年下学期期末": {
            "物理方向总分": "",
            "历史方向总分": "",
            "单科链接": { "⚡ 物理诊断": "" }
        }
    },
    # ==================== 高一 ====================
    "高一": {
        "2026年入学摸底考": {
            "物理方向总分": "",
            "历史方向总分": "",
            "单科链接": { "📐 数学诊断": "" }
        }
    }
}

# ==============================================================================

# --- CSS 美化 & 🖨️ 打印优化 (黑科技) ---
st.markdown("""
<style>
    .metric-card { background-color: #f8f9fa; border-left: 5px solid #1f77b4; padding: 15px; margin-bottom: 10px; border-radius: 5px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); }
    
    /* 打印时的样式设置：隐藏侧边栏、按钮、页脚 */
    @media print {
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stHeader"] { display: none; }
        footer { display: none; }
        .stButton { display: none; }
        [data-testid="stToolbar"] { display: none; }
        
        /* 调整主内容区域宽度，利用纸张全宽 */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏逻辑 ---
with st.sidebar:
    st.title("🏫 全校系统导航")
    
    selected_grade = st.selectbox("1️⃣ 选择年级", list(SCHOOL_DATA.keys()))
    
    grade_exams = SCHOOL_DATA.get(selected_grade, {})
    if not grade_exams:
        st.warning("该年级暂无数据")
        st.stop()
        
    selected_exam_name = st.selectbox("2️⃣ 选择考试场次", list(grade_exams.keys()))
    current_config = grade_exams[selected_exam_name]
    
    st.divider()
    
    direction = st.selectbox("3️⃣ 选择分科方向", ["物理方向", "历史方向"])
    st.divider()

    mode = st.radio("4️⃣ 身份选择", ["👨‍🎓 学生/家长查询", "👨‍🏫 管理者入口"])
    
    if mode == "👨‍🎓 学生/家长查询":
        available_menus = ["📑 成绩查询 (本次)", "📈 历史成绩趋势 (所有)"]
        if current_config:
            for name, url in current_config["单科链接"].items():
                if url and url.strip():
                    available_menus.append(name)
        
        menu = st.radio("功能选择", available_menus)
        
        st.divider()
        st.markdown("### 🔐 学生验证")
        input_name = st.text_input("学生姓名")
        input_id = st.text_input("考号/学号")
        is_admin = False
        
    else:
        st.divider()
        st.markdown("### 🔐 管理员登录")
        pwd = st.text_input("请输入密码", type="password")
        
        if pwd == ADMIN_PASSWORD:
            st.success(f"✅ 已进入 {selected_grade} 管理后台")
            is_admin = True
            menu = st.radio("管理面板", ["📊 班级成绩PK", "📈 总体学情概览", "🔍 知识点共性诊断"])
        else:
            if pwd:
                st.error("❌ 密码错误")
            is_admin = False
            menu = None

# --- 函数区 ---

# 1. 通用加载
def load_data(url, header_lines=0):
    try:
        return pd.read_csv(url, header=header_lines, on_bad_lines='skip')
    except:
        return None

# 2. 辅助函数：将DataFrame转为CSV下载
@st.cache_data
def convert_df_to_csv(df):
    # utf-8-sig 用于解决 Excel 打开中文乱码问题
    return df.to_csv(index=False).encode('utf-8-sig')

# 3. 获取学生历史成绩
def get_student_history(grade_data, student_name, student_id, direction):
    history_list = []
    for exam_name, config in grade_data.items():
        url = config.get("物理方向总分") if direction == "物理方向" else config.get("历史方向总分")
        if not url: continue
        df = load_data(url)
        if df is None: continue
        
        id_col = '考号' if '考号' in df.columns else '学号'
        if id_col not in df.columns: continue
        
        df[id_col] = df[id_col].astype(str).str.strip()
        student = df[(df['姓名'].astype(str).str.strip() == student_name.strip()) & 
                     (df[id_col] == student_id.strip())]
        
        if len(student) > 0:
            data = student.iloc[0]
            total = data['总分'] if '总分' in data else 0
            rank = data['班级排名'] if '班级排名' in data else None
            history_list.append({
                "考试名称": exam_name,
                "总分": total,
                "班级排名": rank
            })
    return pd.DataFrame(history_list)

# 4. 渲染单科雷达图
def render_subject_analysis(subject_name, url, student_name, student_id):
    st.header(f"{subject_name} - {selected_exam_name}")
    try:
        df = pd.read_csv(url, header=[0, 1, 2], on_bad_lines='skip')
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
            st.warning(f"本次考试未找到 {student_name} 的数据。")
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
                    st.success("🎉 基础扎实，超过平均水平！")
            
            st.divider()
            
            # --- 📥 导出按钮区 ---
            col_exp1, col_exp2 = st.columns([1, 5])
            with col_exp1:
                csv_data = convert_df_to_csv(df_kp)
                st.download_button(
                    label="📥 下载诊断数据 (Excel)",
                    data=csv_data,
                    file_name=f"{student_name}_{subject_name}_诊断分析.csv",
                    mime='text/csv'
                )
            
            st.dataframe(df_kp, use_container_width=True)

    except Exception as e:
        st.error(f"数据读取失败: {e}")

# ==============================================================================
# 🚀 逻辑分支 A: 管理员模式
# ==============================================================================
if is_admin:
    st.title(f"👨‍🏫 教务后台 - {selected_grade} {selected_exam_name}")
    
    target_url = current_config["物理方向总分"] if direction == "物理方向" else current_config["历史方向总分"]
    
    if menu == "📊 班级成绩PK":
        if not target_url:
            st.warning("暂未配置该场考试的总分表链接。")
        else:
            df = load_data(target_url)
            if df is not None and '班级' in df.columns:
                st.header("🏆 班级平均分对比")
                exclude = ['姓名', '考号', '学号', '班级', '排名', '总分', '班级排名', '年级排名', '序号']
                subjects = []
                for c in df.columns:
                    if c not in exclude and not c.startswith("Unnamed"):
                        df[c] = pd.to_numeric(df[c], errors='coerce')
                        if df[c].notna().sum() > 0:
                            subjects.append(c)

                if not subjects:
                    st.error("未检测到有效成绩列。")
                else:
                    cols_to_calc = subjects + (['总分'] if '总分' in df.columns else [])
                    class_avg = df.groupby('班级')[cols_to_calc].mean().round(1).reset_index()
                    
                    if '总分' in class_avg.columns:
                        fig_total = px.bar(class_avg, x='班级', y='总分', color='班级', text_auto=True, title="各班总平均分")
                        st.plotly_chart(fig_total, use_container_width=True)
                    
                    if subjects:
                        st.subheader("📝 单科平均分")
                        sel_sub = st.selectbox("选择科目", subjects)
                        fig_sub = px.bar(class_avg, x='班级', y=sel_sub, color='班级', text_auto=True, title=f"各班{sel_sub}平均分")
                        st.plotly_chart(fig_sub, use_container_width=True)
                    
                    with st.expander("查看数据表"):
                        st.dataframe(class_avg)
                        # --- 📥 管理员导出 ---
                        csv_admin = convert_df_to_csv(class_avg)
                        st.download_button("📥 下载班级分析表", csv_admin, "class_analysis.csv", "text/csv")
            else:
                st.error("读取失败或缺少【班级】列。")

    elif menu == "📈 总体学情概览":
        if target_url:
            df = load_data(target_url)
            if df is not None:
                if '总分' in df.columns: df['总分'] = pd.to_numeric(df['总分'], errors='coerce')
                c1, c2, c3 = st.columns(3)
                c1.metric("总人数", len(df))
                avg_score = round(df['总分'].mean(), 1) if '总分' in df else "N/A"
                c2.metric("年级均分", avg_score)
                max_score = df['总分'].max() if '总分' in df else "N/A"
                c3.metric("最高分", max_score)
                
                if '总分' in df and df['总分'].notna().sum() > 0:
                    fig_hist = px.histogram(df, x="总分", nbins=20, title="年级总分分布", color_discrete_sequence=['#1f77b4'])
                    st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.warning("未配置链接。")

    elif menu == "🔍 知识点共性诊断":
        st.info(f"分析 {selected_exam_name} 的共性薄弱点。")
        avail_subs = [k for k, v in current_config["单科链接"].items() if v]
        sel_diagnosis = st.selectbox("选择学科", avail_subs)
        
        if sel_diagnosis:
            diag_url = current_config["单科链接"][sel_diagnosis]
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
                    fig_k = px.bar(df_k, x="年级平均掌握率", y="知识点", orientation='h', title=f"{sel_diagnosis} 知识点排行", color="年级平均掌握率", color_continuous_scale='RdYlGn')
                    st.plotly_chart(fig_k, use_container_width=True)
                    st.error(f"🚨 最薄弱点：{df_k.iloc[0]['知识点']} (掌握率 {df_k.iloc[0]['年级平均掌握率']}%)")
                    
                    # --- 📥 管理员导出 ---
                    csv_k = convert_df_to_csv(df_k)
                    st.download_button("📥 下载知识点分析表", csv_k, "knowledge_analysis.csv", "text/csv")
            except:
                st.error("读取失败。")

# ==============================================================================
# 🚀 逻辑分支 B: 学生模式
# ==============================================================================
else:
    if not input_name or not input_id:
        st.info(f"👈 请在左侧输入姓名和考号。")
        st.stop()
        
    # --- 功能：历史成绩趋势 ---
    if menu == "📈 历史成绩趋势 (所有)":
        st.header(f"📈 {input_name} - 历史成绩追踪")
        st.caption(f"年级：{selected_grade} | 方向：{direction}")
        
        grade_data = SCHOOL_DATA.get(selected_grade)
        df_history = get_student_history(grade_data, input_name, input_id, direction)
        
        if not df_history.empty:
            st.markdown("##### 🏆 总分变化趋势")
            fig = px.line(df_history, x='考试名称', y='总分', markers=True, text='总分')
            fig.update_traces(textposition="top center")
            st.plotly_chart(fig, use_container_width=True)
            
            if '班级排名' in df_history.columns and df_history['班级排名'].notna().any():
                st.markdown("##### 🔖 班级排名趋势")
                fig_rank = px.line(df_history, x='考试名称', y='班级排名', markers=True, text='班级排名')
                fig_rank.update_yaxes(autorange="reversed") 
                st.plotly_chart(fig_rank, use_container_width=True)
                
            with st.expander("查看详细历史数据表"):
                st.dataframe(df_history, use_container_width=True)
                
            # --- 📥 导出按钮 ---
            st.divider()
            csv_hist = convert_df_to_csv(df_history)
            st.download_button(
                label="📥 下载历史成绩单 (Excel)",
                data=csv_hist,
                file_name=f"{input_name}_历史成绩.csv",
                mime='text/csv'
            )
        else:
            st.warning("暂未查询到历史记录，请确认姓名考号。")

    # --- 功能：本次成绩查询 ---
    elif menu == "📑 成绩查询 (本次)":
        target_url = current_config["物理方向总分"] if direction == "物理方向" else current_config["历史方向总分"]
        if target_url:
            try:
                df = pd.read_csv(target_url, on_bad_lines='skip')
                id_col = '考号' if '考号' in df.columns else '学号'
                if id_col not in df.columns:
                    st.error("Excel缺少【考号】或【学号】列")
                    st.stop()

                df[id_col] = df[id_col].astype(str).str.strip()
                student = df[(df['姓名'].astype(str).str.strip() == input_name.strip()) & 
                             (df[id_col] == input_id.strip())]
                
                if len(student) == 0:
                    st.error(f"在 {selected_exam_name} 中未找到该学生。")
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
                        
                        # --- 📥 导出按钮 ---
                        csv_score = convert_df_to_csv(chart_data)
                        st.download_button("📥 下载本次成绩单 (Excel)", csv_score, f"{input_name}_本次成绩.csv", "text/csv")

            except Exception as e:
                st.error(f"查询出错: {e}")
        else:
            st.warning("暂未配置该场考试的总分表。")
            
    # --- 功能：单科诊断 ---
    else:
        target_url = current_config["单科链接"].get(menu)
        if target_url:
            render_subject_analysis(menu, target_url, input_name, input_id)