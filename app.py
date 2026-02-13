import streamlit as st
import pandas as pd
import plotly.graph_objects as go # 引入更高级的绘图库
import os

st.set_page_config(page_title="学生全科诊断系统", layout="wide")
st.title('🎓 学生全科能力诊断系统')

# --- 1. 数据加载逻辑 (自动读取 data.xlsx 或 上传) ---
data_file = None
default_file = 'data.xlsx'

with st.sidebar:
    st.header("📂 教师管理")
    uploaded_file = st.file_uploader("更新成绩单", type=["xlsx"])
    if uploaded_file:
        data_file = uploaded_file
    elif os.path.exists(default_file):
        data_file = default_file
        st.success("✅ 已自动加载云端成绩单")

if data_file is None:
    st.warning("请上传 Excel 或在 GitHub 存入 data.xlsx")
    st.stop()

# --- 2. 数据预处理 (智能识别科目) ---
try:
    df = pd.read_excel(data_file)
    df = df.dropna(subset=['姓名']) # 去除空行
    
    # 【核心黑科技】：自动找出哪些列是“科目”
    # 逻辑：排除掉 姓名、学号、总分、排名 等非科目列，剩下的数字列都算科目
    exclude_cols = ['姓名', '学号', '考号', '班级', '学校', '区县', '总分', '总分赋分', '班级排名', '年级排名', '校名']
    
    # 找出所有数字类型的列
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    # 从数字列里，剔除掉上面的 exclude_cols
    subject_cols = [c for c in numeric_cols if c not in exclude_cols]

    if not subject_cols:
        st.error("未找到科目列！请检查Excel表头，确保科目分数为数字格式。")
        st.stop()

    # --- 3. 全班概况 (班级维度的分析) ---
    st.header("📊 班级整体学科分析")
    
    # 计算全班各科平均分
    class_avg = df[subject_cols].mean().round(1)
    
    # 展示各科平均分 (柱状图)
    st.caption("全班各科平均分对比：")
    st.bar_chart(class_avg)

    st.divider()

    # --- 4. 个人全科诊断 (六边形雷达图) ---
    st.header("🔍 学生个人深度诊断")
    
    selected_student = st.selectbox("请选择学生姓名：", df['姓名'].unique())
    
    if selected_student:
        # 取出该学生的数据
        student_data = df[df['姓名'] == selected_student].iloc[0]
        
        # 准备画图数据
        student_scores = [student_data[sub] for sub in subject_cols] # 学生的每科分数
        avg_scores = [class_avg[sub] for sub in subject_cols]       # 班级的每科平均分
        
        # 为了让雷达图闭合，需要把第一个数据重复加到最后
        plot_subjects = subject_cols + [subject_cols[0]]
        plot_student_scores = student_scores + [student_scores[0]]
        plot_avg_scores = avg_scores + [avg_scores[0]]

        # --- 开始画雷达图 ---
        fig = go.Figure()

        # 画第一层：班级平均线 (作为参考标准，灰色)
        fig.add_trace(go.Scatterpolar(
            r=plot_avg_scores,
            theta=plot_subjects,
            fill='toself',
            name='班级平均水平',
            line_color='gray',
            opacity=0.4
        ))

        # 画第二层：学生个人线 (蓝色，高亮)
        fig.add_trace(go.Scatterpolar(
            r=plot_student_scores,
            theta=plot_subjects,
            fill='toself',
            name=f'{selected_student} 的成绩',
            line_color='#1f77b4'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(max(plot_student_scores), max(plot_avg_scores)) + 10] # 自动调整刻度范围
                )),
            showlegend=True,
            title=f"【{selected_student}】 学科能力雷达图"
        )
        
        # 左右布局：左边放图，右边放具体的表格
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.plotly_chart(fig, use_container_width=True)
            if '总分' in df.columns or '总分赋分' in df.columns:
                 total_col = '总分' if '总分' in df.columns else '总分赋分'
                 st.metric("总分", student_data[total_col])

        with col2:
            st.subheader("📝 单科详细诊断")
            # 制作一个对比表格
            comparison_data = []
            for sub in subject_cols:
                score = student_data[sub]
                avg = class_avg[sub]
                diff = score - avg
                status = "🟢 优势" if diff > 0 else "🔴 需努力"
                comparison_data.append({
                    "科目": sub,
                    "我的分数": score,
                    "班级平均": avg,
                    "差值": f"{diff:+.1f}",
                    "状态": status
                })
            
            st.dataframe(pd.DataFrame(comparison_data), hide_index=True)

except Exception as e:
    st.error(f"发生错误：{e}")
    st.info("请检查Excel中是否包含非数字的干扰列，或者表头是否正确。")