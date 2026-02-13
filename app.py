import streamlit as st
import pandas as pd
import plotly.express as px

# 设置网页标题和布局
st.set_page_config(page_title="学生成绩测评系统", layout="wide")

st.title('🎓 学生成绩智能测评系统')

# 侧边栏：上传文件
with st.sidebar:
    st.header("📂 教师管理后台")
    uploaded_file = st.file_uploader("请上传成绩单 Excel", type=["xlsx"])
    st.info("💡 提示：Excel 需包含 '姓名' 和 '总分赋分' 列")

if uploaded_file is not None:
    # 1. 读取数据
    df = pd.read_excel(uploaded_file)
    df = df.dropna(subset=['姓名']) # 清除空行
    
    # 自动计算全班排名 (从高到低)
    if '总分赋分' in df.columns:
        df['班级排名'] = df['总分赋分'].rank(ascending=False, method='min')
    
    # --- 第一部分：全班概况 (老师看) ---
    st.header("📊 全班考情分析")
    
    # 过滤掉 0 分（缺考）来计算平均分，这样更准确
    valid_scores = df[df['总分赋分'] > 0]
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("参考人数", len(df))
    kpi2.metric("班级平均分", f"{valid_scores['总分赋分'].mean():.1f}")
    kpi3.metric("最高分", int(df['总分赋分'].max()))
    kpi4.metric("及格率 (≥360)", f"{(len(df[df['总分赋分']>=360])/len(df)*100):.1f}%")

    # 折叠显示图表，让界面更清爽
    with st.expander("点击查看分数分布图", expanded=True):
        fig = px.histogram(df, x='总分赋分', nbins=20, title="成绩分布直方图", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

    st.divider() # 分割线

    # --- 第二部分：个人查询 (学生/家长看) ---
    st.header("🔍 学生个人查分")
    
    # 搜索框：选择学生姓名
    student_list = df['姓名'].unique().tolist()
    selected_student = st.selectbox("请选择或输入学生姓名：", student_list)
    
    if selected_student:
        # 找到该学生的那一行数据
        student_data = df[df['姓名'] == selected_student].iloc[0]
        my_score = student_data['总分赋分']
        my_rank = int(student_data['班级排名'])
        
        # 你的成绩单卡片
        st.success(f"正在查看 【{selected_student}】 的成绩报告")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("我的总分", my_score)
        # 根据排名显示不同颜色（前10名显示绿色奖杯）
        col2.metric("班级排名", f"第 {my_rank} 名", delta="🏆 优秀" if my_rank <= 10 else None)
        
        # 专家级分析：计算超过了多少人
        beat_ratio = len(df[df['总分赋分'] < my_score]) / len(df) * 100
        col3.progress(beat_ratio / 100, text=f"击败了全班 {beat_ratio:.1f}% 的同学")
        
        # 显示详细数据表（只显示该生）
        st.caption("详细数据：")
        st.dataframe(df[df['姓名'] == selected_student])

else:
    st.write("👈 请在左侧上传 Excel 文件开始分析")
