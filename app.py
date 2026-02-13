import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="学生成绩查询系统", layout="wide")

# --- 1. 数据加载与工作表识别 ---
data_file = None
default_file = 'data.xlsx'

# 侧边栏：教师上传通道
with st.sidebar:
    st.header("🔐 教师通道")
    password = st.text_input("输入管理员密码解锁", type="password")
    if password == "123456": 
        uploaded_file = st.file_uploader("更新成绩单 (支持多Sheet)", type=["xlsx"])
        if uploaded_file:
            data_file = uploaded_file
            st.success("数据已更新")
    st.info("家长仅能查询，无法查看此栏。")

if os.path.exists(default_file) and data_file is None:
    data_file = default_file

if data_file is None:
    st.warning("系统维护中，请联系老师上传数据。")
    st.stop()

# --- 2. 核心逻辑：读取 Excel 的所有工作表 ---
try:
    # 使用 ExcelFile 这种高级方式，先不读数据，只读“目录”
    xls = pd.ExcelFile(data_file)
    sheet_names = xls.sheet_names # 获取所有工作表的名字，例如 ['物理方向', '历史方向']

    st.title('🎓 学生成绩安全查询系统')
    st.write("请先选择所属方向，然后输入身份信息进行验证：")

    # --- 3. 家长查询界面 ---
    with st.form("query_form"):
        # 增加一个下拉菜单，让家长选择方向
        selected_sheet = st.selectbox("第一步：请选择分科方向", sheet_names)
        
        col_input1, col_input2 = st.columns(2)
        input_name = col_input1.text_input("第二步：请输入学生姓名")
        input_id = col_input2.text_input("第三步：请输入考号/学号")
        
        submitted = st.form_submit_button("🔍 立即查询", use_container_width=True)

    # --- 4. 验证与展示逻辑 ---
    if submitted:
        if input_name and input_id:
            # 【关键修改】：只读取用户选中的那个工作表
            df = pd.read_excel(data_file, sheet_name=selected_sheet)
            df = df.dropna(subset=['姓名']) 
            
            # 自动处理考号格式
            id_col = '考号' if '考号' in df.columns else '学号'
            if id_col not in df.columns:
                st.error(f"在【{selected_sheet}】表中未找到【考号】或【学号】列！")
                st.stop()
                
            df[id_col] = df[id_col].astype(str).str.strip()
            df['姓名'] = df['姓名'].astype(str).str.strip()

            # 验证查询
            result = df[(df['姓名'] == input_name) & (df[id_col] == input_id)]
            
            if len(result) == 0:
                st.error(f"❌ 查询失败：在【{selected_sheet}】中未找到该学生，请检查方向是否选对？")
            else:
                st.success(f"✅ 验证通过！正在显示【{selected_sheet} - {input_name}】的成绩")
                student_data = result.iloc[0]

                # --- 智能识别该方向的科目 ---
                exclude_cols = ['姓名', '学号', '考号', '班级', '学校', '区县', '校名', '总分', '总分赋分', '班级排名', '年级排名', 'Unnamed', '序号']
                subject_cols = []
                for col in df.columns:
                    if col not in exclude_cols and not str(col).startswith('Unnamed'):
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        if df[col].notna().sum() > 0:
                            subject_cols.append(col)
                
                # 计算该方向的平均分
                class_avg = df[subject_cols].mean().round(1)

                # 提取个人成绩
                my_subjects = []
                my_scores = []
                class_scores = []
                for sub in subject_cols:
                    score = student_data[sub]
                    if pd.notna(score) and score > 0:
                        my_subjects.append(sub)
                        my_scores.append(score)
                        class_scores.append(class_avg[sub])
                
                if not my_subjects:
                    st.warning("无有效成绩数据。")
                else:
                    total_score = sum(my_scores)
                    
                    # 展示成绩卡片
                    st.markdown("### 📄 成绩概览")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("姓名", input_name)
                    c2.metric("方向", selected_sheet) # 显示他选的方向
                    c3.metric("总分", f"{total_score:.1f}")

                    st.divider()

                    # 图表与明细
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
                            polar=dict(radialaxis=dict(visible=True)),
                            margin=dict(t=20, b=20, l=20, r=20),
                            height=350,
                            legend=dict(orientation="h", y=-0.1)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with col_table:
                        st.markdown("**📝 单科得分明细**")
                        score_data = []
                        for sub, score, avg in zip(my_subjects, my_scores, class_scores):
                            score_data.append({
                                "科目": sub,
                                "我的分数": score,
                                "方向平均": avg,
                                "状态": "🟢" if score >= avg else "🔴"
                            })
                        st.dataframe(pd.DataFrame(score_data), hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"读取Excel出错，请确保文件包含正确的工作表: {e}")