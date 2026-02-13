import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- 页面设置 ---
st.set_page_config(page_title="学生成绩查询系统", layout="wide")

# ==============================================================================
# 👇👇👇 请在这里填入您的谷歌表格链接 (保留双引号，不要换行) 👇👇👇
# ==============================================================================

PHYSICS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRyhhA4C2A9hp-2165uyRgqheKfCccT5NN0dp_FOW2Jl8FE4VmAMPajsWKiTEOCcqIxhIDnuIUwOoQ0/pub?gid=0&single=true&output=csv" # 👈 替换物理方向链接
HISTORY_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRyhhA4C2A9hp-2165uyRgqheKfCccT5NN0dp_FOW2Jl8FE4VmAMPajsWKiTEOCcqIxhIDnuIUwOoQ0/pub?gid=1671669597&single=true&output=csv" # 👈 替换历史方向链接

# ==============================================================================

# --- 侧边栏 ---
with st.sidebar:
    st.header("ℹ️ 系统说明")
    st.info("本系统数据已接入云端，家长可直接查询。")
    st.caption("🔒 数据安全保护中")

# --- 主界面 ---
st.title('🎓 学生成绩安全查询系统')
st.markdown("### 请输入信息进行验证查询")

with st.form("query_form"):
    direction_options = ["物理方向", "历史方向"]
    selected_sheet = st.selectbox("第一步：请选择分科方向", direction_options)
    
    col1, col2 = st.columns(2)
    input_name = col1.text_input("第二步：请输入学生姓名")
    input_id = col2.text_input("第三步：请输入考号/学号")
    
    submitted = st.form_submit_button("🔍 立即查询", use_container_width=True)

# --- 核心逻辑 ---
if submitted:
    if not input_name or not input_id:
        st.warning("⚠️ 请完整填写姓名和考号！")
        st.stop()

    # 1. 确定链接
    if selected_sheet == '物理方向':
        target_url = PHYSICS_URL
    else:
        target_url = HISTORY_URL

    try:
        # 读取数据
        df = pd.read_csv(target_url, on_bad_lines='skip')
        
        # 【修复1】强力清洗表头 (去除所有列名的空格)
        df.columns = df.columns.str.strip()
        
    except Exception as e:
        st.error(f"❌ 无法连接数据源，请检查链接。错误信息: {e}")
        st.stop()

    # 2. 数据预处理
    try:
        df = df.dropna(subset=['姓名']) 
        
        # 自动识别考号
        id_col = '考号' if '考号' in df.columns else '学号'
        if id_col not in df.columns:
            st.error("数据表中未找到【考号】或【学号】列！")
            st.stop()
            
        # 格式化验证信息
        df[id_col] = df[id_col].astype(str).str.strip()
        df['姓名'] = df['姓名'].astype(str).str.strip()
        input_name = input_name.strip()
        input_id = input_id.strip()

        # 3. 验证身份
        result = df[(df['姓名'] == input_name) & (df[id_col] == input_id)]
        
        if len(result) == 0:
            st.error(f"❌ 查询失败：在【{selected_sheet}】中未找到该学生。")
        else:
            st.success(f"✅ 验证通过！正在显示 {input_name} 的成绩报告")
            student_data = result.iloc[0]

            # 4. 智能识别科目 (强制转数字)
            exclude_cols = ['姓名', '学号', '考号', '班级', '学校', '区县', '校名', '总分', '总分赋分', '班级排名', '年级排名', 'Unnamed', '序号', 'id', 'ID']
            subject_cols = []
            
            for col in df.columns:
                if col not in exclude_cols and not str(col).startswith('Unnamed'):
                    # 尝试转换，非数字变NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    if df[col].notna().sum() > 0:
                        subject_cols.append(col)
            
            # 计算平均分
            class_avg = df[subject_cols].mean().round(1)

            # 5. 提取个人成绩 (【修复2】最关键的一步)
            my_subjects = []
            my_scores = []
            class_scores = []
            
            for sub in subject_cols:
                # 获取分数，并强制转为浮点数，如果是NaN则给0
                raw_score = pd.to_numeric(student_data[sub], errors='coerce')
                
                # 只有分数有效才显示
                if pd.notna(raw_score) and raw_score >= 0:
                    my_subjects.append(sub)
                    my_scores.append(raw_score) # 这里存进去的一定是数字了
                    class_scores.append(class_avg[sub])
            
            if not my_subjects:
                st.warning("该学生没有有效成绩数据。")
            else:
                total_score = sum(my_scores)
                
                # --- 展示部分 ---
                st.markdown("### 📄 成绩概览")
                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric("姓名", input_name)
                kpi2.metric("方向", selected_sheet)
                kpi3.metric("总分", f"{total_score:.1f}")

                st.divider()

                col_chart, col_table = st.columns([1, 1])
                
                with col_chart:
                    st.markdown("**📊 能力雷达图**")
                    plot_subjects = my_subjects + [my_subjects[0]]
                    plot_my_scores = my_scores + [my_scores[0]]
                    plot_class_scores = class_scores + [class_scores[0]]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=plot_class_scores, theta=plot_subjects, fill='toself',
                        name='方向平均', line_color='#cccccc', opacity=0.4
                    ))
                    fig.add_trace(go.Scatterpolar(
                        r=plot_my_scores, theta=plot_subjects, fill='toself',
                        name='我的成绩', line_color='#1f77b4'
                    ))
                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, max(max(plot_my_scores), max(plot_class_scores)) + 10])),
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=350,
                        legend=dict(orientation="h", y=-0.1)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col_table:
                    st.markdown("**📝 单科得分明细**")
                    score_data = []
                    # 因为 my_scores 已经是强制转换过的数字，这里对比绝对不会报错了
                    for sub, score, avg in zip(my_subjects, my_scores, class_scores):
                        status = "🟢" if score >= avg else "🔴"
                        score_data.append({
                            "科目": sub,
                            "我的分数": score,
                            "方向平均": avg,
                            "对比": status
                        })
                    st.dataframe(pd.DataFrame(score_data), hide_index=True, use_container_width=True)

    except Exception as e:
        st.error(f"数据处理出错: {e}")
