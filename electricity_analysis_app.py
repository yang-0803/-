
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'WenQuanYi Zen Hei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 页面配置
st.set_page_config(
    page_title="2023年1月用电数据分析平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------
# 1. 数据加载与预处理
# ----------------------
@st.cache_data(ttl=3600)  # 缓存数据，1小时过期
def load_and_preprocess_data():
    """加载和预处理数据"""
    # 读取数据
    df = pd.read_csv('2023年1月.csv')
    
    # 数据预处理
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['日期'] = df['timestamp'].dt.date
    df['小时'] = df['timestamp'].dt.hour
    df['星期名称'] = df['timestamp'].dt.day_name()
    
    # 映射星期数字到中文
    week_map = {1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 0: '周日'}
    df['星期中文'] = df['星期'].map(week_map)
    
    # 提取关键分类列
    # 区域供电局
    area_columns = [col for col in df.columns if '供电局' in col and col != '深汕特别合作区供电局']
    area_columns.append('总计')
    
    # 产业用电分类
    industry_columns = [
        '全社会用电总计',
        '　A、全行业用电合计',
        '　　第一产业',
        '　　第二产业',
        '　　第三产业',
        '　B、城乡居民生活用电合计',
        '　　城镇居民',
        '　　乡村居民'
    ]
    
    # 过滤存在的列
    industry_columns = [col for col in industry_columns if col in df.columns]
    
    return df, area_columns, industry_columns

# 加载数据
df, area_columns, industry_columns = load_and_preprocess_data()

# ----------------------
# 2. 侧边栏导航
# ----------------------
st.sidebar.title("📊 2023年1月用电数据分析")
st.sidebar.markdown("---")

# 页面选择
page_options = [
    "首页数据概览",
    "区域用电分析", 
    "产业用电分析",
    "时间趋势分析",
    "原始数据查看"
]
selected_page = st.sidebar.radio("选择分析页面", page_options)

# 时间范围选择器
st.sidebar.markdown("---")
st.sidebar.subheader("⏰ 时间筛选")

# 获取数据的时间范围
min_date = df['timestamp'].min().date()
max_date = df['timestamp'].max().date()

# 日期选择器
selected_dates = st.sidebar.date_input(
    "选择日期范围",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# 转换为datetime用于筛选
start_date = pd.to_datetime(selected_dates[0])
end_date = pd.to_datetime(selected_dates[1]) + timedelta(days=1) - timedelta(seconds=1)

# 筛选数据
filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)].copy()

# 显示数据基本信息
st.sidebar.markdown("---")
st.sidebar.subheader("📋 数据信息")
st.sidebar.text(f"总记录数: {len(filtered_df):,} 条")
st.sidebar.text(f"时间跨度: {selected_dates[0]} 至 {selected_dates[1]}")
st.sidebar.text(f"覆盖天数: {(selected_dates[1] - selected_dates[0]).days + 1} 天")

# ----------------------
# 3. 首页数据概览
# ----------------------
if selected_page == "首页数据概览":
    st.title("🏠 2023年1月用电数据总览")
    st.markdown("---")
    
    # 关键指标卡片
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. 总用电量
    total_electricity = filtered_df['总计'].dropna().sum()
    col1.metric("总用电量", f"{total_electricity/1e8:.2f} 亿单位", 
                help="筛选时间段内的总用电量")
    
    # 2. 日均用电量
    valid_days = filtered_df['日期'].nunique()
    daily_avg = total_electricity / valid_days if valid_days > 0 else 0
    col2.metric("日均用电量", f"{daily_avg/1e6:.2f} 百万单位",
                help="筛选时间段内的日均用电量")
    
    # 3. 最大用电负荷
    max_load = filtered_df['总计'].dropna().max()
    col3.metric("最大用电负荷", f"{max_load/1e6:.2f} 百万单位",
                help="筛选时间段内的最大用电负荷")
    
    # 4. 居民生活用电占比
    residential_electricity = filtered_df['　B、城乡居民生活用电合计'].dropna().sum()
    residential_ratio = (residential_electricity / total_electricity * 100) if total_electricity > 0 else 0
    col4.metric("居民生活用电占比", f"{residential_ratio:.1f}%",
                help="居民生活用电占总用电量的比例")
    
    st.markdown("---")
    
    # 主要图表区域
    st.subheader("📈 核心用电趋势")
    
    # 图表1: 用电总量时间趋势
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 左侧：日用电量趋势
    daily_data = filtered_df.groupby('日期')['总计'].agg(['sum', 'mean']).reset_index()
    daily_data['日期'] = pd.to_datetime(daily_data['日期'])
    
    ax1.plot(daily_data['日期'], daily_data['sum']/1e6, 
             marker='o', linewidth=2, markersize=4, color='#2E86AB')
    ax1.set_title('日用电量趋势', fontsize=14, fontweight='bold')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('用电量 (百万单位)')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # 右侧：各产业用电占比饼图
    industry_data = []
    industry_labels = []
    
    # 第二产业
    secondary = filtered_df['　　第二产业'].dropna().sum()
    if secondary > 0:
        industry_data.append(secondary)
        industry_labels.append('第二产业')
    
    # 第三产业
    tertiary = filtered_df['　　第三产业'].dropna().sum()
    if tertiary > 0:
        industry_data.append(tertiary)
        industry_labels.append('第三产业')
    
    # 居民生活
    residential = filtered_df['　B、城乡居民生活用电合计'].dropna().sum()
    if residential > 0:
        industry_data.append(residential)
        industry_labels.append('居民生活用电')
    
    # 第一产业
    primary = filtered_df['　　第一产业'].dropna().sum()
    if primary > 0:
        industry_data.append(primary)
        industry_labels.append('第一产业')
    
    # 绘制饼图
    colors = ['#A23B72', '#F18F01', '#C73E1D', '#2E86AB']
    wedges, texts, autotexts = ax2.pie(industry_data, labels=industry_labels, autopct='%1.1f%%',
                                       colors=colors[:len(industry_data)], startangle=90)
    ax2.set_title('各产业用电占比', fontsize=14, fontweight='bold')
    
    # 美化饼图文字
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    st.pyplot(fig1, use_container_width=True)
    
    st.markdown("---")
    
    # 区域用电排名
    st.subheader("🏙️ 各区域用电排名")
    
    # 计算各区域总用电量
    area_data = []
    for area in area_columns:
        if area != '总计' and area in filtered_df.columns:
            area_total = filtered_df[area].dropna().sum()
            if area_total > 0:
                area_data.append({
                    '区域': area.replace('供电局', ''),
                    '总用电量': area_total,
                    '占比': (area_total / total_electricity * 100) if total_electricity > 0 else 0
                })
    
    area_df = pd.DataFrame(area_data)
    area_df = area_df.sort_values('总用电量', ascending=False)
    
    # 创建排名图表
    fig2, ax = plt.subplots(figsize=(12, 8))
    
    bars = ax.barh(area_df['区域'][::-1], area_df['总用电量'][::-1]/1e6, 
                   color='#2E86AB', alpha=0.8)
    
    # 在条形图上添加数值标签
    for i, (bar, value, ratio) in enumerate(zip(bars, area_df['总用电量'][::-1]/1e6, 
                                               area_df['占比'][::-1])):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{value:.1f} 百万单位 ({ratio:.1f}%)',
                va='center', fontweight='bold', fontsize=10)
    
    ax.set_title('各区域用电总量排名', fontsize=14, fontweight='bold')
    ax.set_xlabel('用电量 (百万单位)')
    ax.set_ylabel('区域')
    ax.grid(True, alpha=0.3, axis='x')
    
    st.pyplot(fig2, use_container_width=True)

# ----------------------
# 4. 区域用电分析
# ----------------------
elif selected_page == "区域用电分析":
    st.title("🏙️ 区域用电详细分析")
    st.markdown("---")
    
    # 选择区域
    area_options = [area.replace('供电局', '') for area in area_columns if area != '总计']
    selected_areas = st.multiselect(
        "选择要分析的区域 (可多选)",
        options=area_options,
        default=area_options[:3]  # 默认选择前3个区域
    )
    
    if not selected_areas:
        st.warning("请至少选择一个区域进行分析")
    else:
        # 转换回原始列名
        selected_area_cols = [area + '供电局' for area in selected_areas]
        
        st.markdown("---")
        
        # 1. 区域用电趋势对比
        st.subheader("📈 区域用电趋势对比")
        
        fig3, ax = plt.subplots(figsize=(14, 8))
        
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#7209B7', '#6A994E', '#BC6C25', '#386641', '#BC4749', '#F2E8CF']
        
        for i, (area, col) in enumerate(zip(selected_areas, selected_area_cols)):
            if col in filtered_df.columns:
                # 按日期聚合
                daily_area = filtered_df.groupby('日期')[col].sum().reset_index()
                daily_area['日期'] = pd.to_datetime(daily_area['日期'])
                
                ax.plot(daily_area['日期'], daily_area[col]/1e6, 
                        marker='o', linewidth=2, markersize=4, 
                        label=area, color=colors[i % len(colors)])
        
        ax.set_title('各区域日用电量趋势对比', fontsize=14, fontweight='bold')
        ax.set_xlabel('日期')
        ax.set_ylabel('用电量 (百万单位)')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        
        st.pyplot(fig3, use_container_width=True)
        
        st.markdown("---")
        
        # 2. 区域用电时段分析
        st.subheader("⏰ 区域用电时段分布")
        
        # 计算各时段平均用电量
        time_period_data = []
        
        for area, col in zip(selected_areas, selected_area_cols):
            if col in filtered_df.columns:
                # 按小时分组计算平均值
                hourly_data = filtered_df.groupby('小时')[col].mean().reset_index()
                
                for _, row in hourly_data.iterrows():
                    time_period_data.append({
                        '区域': area,
                        '小时': int(row['小时']),
                        '平均用电量': row[col]
                    })
        
        time_period_df = pd.DataFrame(time_period_data)
        
        # 创建热力图数据
        pivot_df = time_period_df.pivot(index='小时', columns='区域', values='平均用电量')
        
        fig4, ax = plt.subplots(figsize=(14, 10))
        
        im = ax.imshow(pivot_df.values, cmap='YlOrRd', aspect='auto')
        
        # 设置坐标轴
        ax.set_xticks(range(len(pivot_df.columns)))
        ax.set_xticklabels(pivot_df.columns)
        ax.set_yticks(range(len(pivot_df.index)))
        ax.set_yticklabels([f'{h}:00' for h in pivot_df.index])
        
        ax.set_xlabel('区域', fontsize=12)
        ax.set_ylabel('时段', fontsize=12)
        ax.set_title('各区域用电时段热力图 (平均用电量)', fontsize=14, fontweight='bold')
        
        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('平均用电量 (单位)', rotation=270, labelpad=20)
        
        # 在每个格子上添加数值
        for i in range(len(pivot_df.index)):
            for j in range(len(pivot_df.columns)):
                if not np.isnan(pivot_df.values[i, j]):
                    text = ax.text(j, i, f'{pivot_df.values[i, j]/1e4:.1f}万',
                                   ha="center", va="center", color="black", fontsize=8)
        
        st.pyplot(fig4, use_container_width=True)
        
        st.markdown("---")
        
        # 3. 区域用电统计表格
        st.subheader("📊 区域用电统计详情")
        
        area_stats = []
        for area, col in zip(selected_areas, selected_area_cols):
            if col in filtered_df.columns:
                area_data = filtered_df[col].dropna()
                if len(area_data) > 0:
                    area_stats.append({
                        '区域': area,
                        '总用电量': f"{area_data.sum()/1e6:.2f} 百万单位",
                        '日均用电量': f"{area_data.sum()/valid_days/1e4:.2f} 万单位",
                        '最大负荷': f"{area_data.max()/1e4:.2f} 万单位",
                        '最小负荷': f"{area_data.min()/1e4:.2f} 万单位",
                        '平均负荷': f"{area_data.mean()/1e4:.2f} 万单位"
                    })
        
        stats_df = pd.DataFrame(area_stats)
        st.dataframe(stats_df, use_container_width=True)

# ----------------------
# 5. 产业用电分析
# ----------------------
elif selected_page == "产业用电分析":
    st.title("🏭 产业用电详细分析")
    st.markdown("---")
    
    # 选择产业类型
    industry_options = [
        ('　　第一产业', '第一产业'),
        ('　　第二产业', '第二产业'),
        ('　　第三产业', '第三产业'),
        ('　B、城乡居民生活用电合计', '居民生活用电'),
        ('全社会用电总计', '全社会用电总计')
    ]
    
    # 过滤存在的产业选项
    available_industries = []
    for col, name in industry_options:
        if col in filtered_df.columns:
            available_industries.append((col, name))
    
    # 多选产业
    selected_industry_cols = st.multiselect(
        "选择要分析的产业类型 (可多选)",
        options=[name for _, name in available_industries],
        default=[name for _, name in available_industries[:3]]  # 默认前3个
    )
    
    # 映射回原始列名
    selected_cols_mapping = {name: col for col, name in available_industries}
    selected_cols = [selected_cols_mapping[name] for name in selected_industry_cols]
    
    if not selected_cols:
        st.warning("请至少选择一个产业类型进行分析")
    else:
        # 1. 产业用电趋势对比
        st.subheader("📈 各产业用电趋势对比")
        
        fig5, ax = plt.subplots(figsize=(14, 8))
        
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#7209B7']
        
        for i, (col, name) in enumerate(zip(selected_cols, selected_industry_cols)):
            # 按日期聚合
            daily_industry = filtered_df.groupby('日期')[col].sum().reset_index()
            daily_industry['日期'] = pd.to_datetime(daily_industry['日期'])
            
            ax.plot(daily_industry['日期'], daily_industry[col]/1e6, 
                    marker='o', linewidth=2, markersize=4, 
                    label=name, color=colors[i % len(colors)])
        
        ax.set_title('各产业日用电量趋势对比', fontsize=14, fontweight='bold')
        ax.set_xlabel('日期')
        ax.set_ylabel('用电量 (百万单位)')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        
        st.pyplot(fig5, use_container_width=True)
        
        st.markdown("---")
        
        # 2. 产业用电结构分析
        st.subheader("📊 产业用电结构分析")
        
        # 计算各产业总用电量
        industry_totals = []
        total_all = 0
        
        for col, name in zip(selected_cols, selected_industry_cols):
            if col in filtered_df.columns:
                industry_total = filtered_df[col].dropna().sum()
                industry_totals.append({
                    '产业': name,
                    '总用电量': industry_total,
                    '占比': 0  # 先初始化
                })
                total_all += industry_total
        
        # 计算占比
        for item in industry_totals:
            if total_all > 0:
                item['占比'] = (item['总用电量'] / total_all) * 100
        
        industry_df = pd.DataFrame(industry_totals)
        industry_df = industry_df.sort_values('总用电量', ascending=False)
        
        # 创建子图
        fig6, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 左侧：柱状图
        bars = ax1.bar(industry_df['产业'], industry_df['总用电量']/1e6, 
                       color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#7209B7'][:len(industry_df)])
        
        # 添加数值标签
        for bar, value, ratio in zip(bars, industry_df['总用电量']/1e6, industry_df['占比']):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{value:.1f} 百万单位\n({ratio:.1f}%)',
                    ha='center', va='bottom', fontweight='bold')
        
        ax1.set_title('各产业用电总量对比', fontsize=14, fontweight='bold')
        ax1.set_xlabel('产业类型')
        ax1.set_ylabel('用电量 (百万单位)')
        ax1.grid(True, alpha=0.3, axis='y')
        plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
        
        # 右侧：堆积面积图（按星期）
        weekday_data = filtered_df.groupby('星期中文')[selected_cols].sum()
        # 确保星期顺序正确
        weekday_order = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        weekday_data = weekday_data.reindex(weekday_order)
        
        # 绘制堆积面积图
        ax2.stackplot(weekday_data.index, 
                     [weekday_data[col]/1e6 for col in selected_cols],
                     labels=selected_industry_cols,
                     alpha=0.8,
                     colors=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#7209B7'][:len(selected_cols)])
        
        ax2.set_title('各产业按星期用电分布', fontsize=14, fontweight='bold')
        ax2.set_xlabel('星期')
        ax2.set_ylabel('总用电量 (百万单位)')
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)
        
        st.pyplot(fig6, use_container_width=True)
        
        st.markdown("---")
        
        # 3. 产业用电统计表格
        st.subheader("📋 产业用电统计详情")
        
        industry_stats = []
        for col, name in zip(selected_cols, selected_industry_cols):
            if col in filtered_df.columns:
                industry_data = filtered_df[col].dropna()
                if len(industry_data) > 0:
                    industry_stats.append({
                        '产业类型': name,
                        '总用电量': f"{industry_data.sum()/1e6:.2f} 百万单位",
                        '日均用电量': f"{industry_data.sum()/valid_days/1e4:.2f} 万单位",
                        '最大负荷': f"{industry_data.max()/1e4:.2f} 万单位",
                        '最小负荷': f"{industry_data.min()/1e4:.2f} 万单位",
                        '平均负荷': f"{industry_data.mean()/1e4:.2f} 万单位",
                        '占总用电比': f"{(industry_data.sum()/total_electricity*100):.1f}%" if total_electricity > 0 else "N/A"
                    })
        
        industry_stats_df = pd.DataFrame(industry_stats)
        st.dataframe(industry_stats_df, use_container_width=True)

# ----------------------
# 6. 时间趋势分析
# ----------------------
elif selected_page == "时间趋势分析":
    st.title("⏰ 时间趋势深度分析")
    st.markdown("---")
    
    # 选择分析维度
    st.subheader("选择分析维度")
    
    col1, col2 = st.columns(2)
    
    # 指标选择
    metric_options = [
        ('总计', '总用电量'),
        ('　　第二产业', '第二产业用电'),
        ('　　第三产业', '第三产业用电'),
        ('　B、城乡居民生活用电合计', '居民生活用电')
    ]
    
    # 过滤可用指标
    available_metrics = []
    for col, name in metric_options:
        if col in filtered_df.columns:
            available_metrics.append((col, name))
    
    selected_metric_col = col1.selectbox(
        "选择用电指标",
        options=[name for _, name in available_metrics],
        index=0
    )
    
    # 映射回原始列名
    metric_col = [col for col, name in available_metrics if name == selected_metric_col][0]
    
    # 时间粒度选择
    time_granularity = col2.selectbox(
        "选择时间粒度",
        options=['小时', '日', '星期', '时段'],
        index=1
    )
    
    st.markdown("---")
    
    # 根据时间粒度生成不同的分析
    if time_granularity == '小时':
        # 小时级趋势分析
        st.subheader("📊 小时级用电趋势分析")
        
        # 按小时聚合
        hourly_data = filtered_df.groupby(['日期', '小时'])[metric_col].mean().reset_index()
        hourly_data['datetime'] = pd.to_datetime(hourly_data['日期'].astype(str) + ' ' + 
                                               hourly_data['小时'].astype(str) + ':00:00')
        
        fig7, ax = plt.subplots(figsize=(16, 8))
        
        # 绘制小时级曲线
        ax.plot(hourly_data['datetime'], hourly_data[metric_col]/1e4, 
                linewidth=1.5, color='#2E86AB', alpha=0.8)
        
        # 添加趋势线
        z = np.polyfit(range(len(hourly_data)), hourly_data[metric_col]/1e4, 1)
        p = np.poly1d(z)
        ax.plot(hourly_data['datetime'], p(range(len(hourly_data))), 
                "r--", linewidth=2, label=f'趋势线 (斜率: {z[0]:.4f})')
        
        ax.set_title(f'{selected_metric_col} - 小时级变化趋势', fontsize=14, fontweight='bold')
        ax.set_xlabel('时间')
        ax.set_ylabel('平均用电量 (万单位)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        st.pyplot(fig7, use_container_width=True)
        
        # 工作日vs周末对比
        st.markdown("---")
        st.subheader("📅 工作日 vs 周末用电对比")
        
        # 区分工作日和周末
        filtered_df['是否工作日'] = filtered_df['是否周末'].apply(lambda x: '周末' if x == 1 else '工作日')
        
        # 按是否工作日和小时聚合
        workday_hourly = filtered_df.groupby(['是否工作日', '小时'])[metric_col].mean().reset_index()
        
        fig8, ax = plt.subplots(figsize=(14, 8))
        
        # 绘制两条曲线
        for workday in ['工作日', '周末']:
            data = workday_hourly[workday_hourly['是否工作日'] == workday]
            ax.plot(data['小时'], data[metric_col]/1e4, 
                    marker='o', linewidth=2, markersize=6, 
                    label=workday)
        
        ax.set_title(f'{selected_metric_col} - 工作日与周末小时用电模式对比', fontsize=14, fontweight='bold')
        ax.set_xlabel('小时')
        ax.set_ylabel('平均用电量 (万单位)')
        ax.set_xticks(range(0, 24))
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        st.pyplot(fig8, use_container_width=True)
    
    elif time_granularity == '日':
        # 日级趋势分析
        st.subheader("📊 日级用电趋势分析")
        
        # 按日期聚合
        daily_data = filtered_df.groupby('日期')[metric_col].agg(['sum', 'mean', 'max', 'min']).reset_index()
        daily_data['日期'] = pd.to_datetime(daily_data['日期'])
        
        fig9, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
        
        # 上图：日总用电量
        ax1.plot(daily_data['日期'], daily_data['sum']/1e6, 
                 marker='o', linewidth=2, markersize=6, color='#2E86AB')
        ax1.fill_between(daily_data['日期'], daily_data['sum']/1e6, alpha=0.3, color='#2E86AB')
        ax1.set_title(f'{selected_metric_col} - 日总用电量趋势', fontsize=14, fontweight='bold')
        ax1.set_ylabel('总用电量 (百万单位)')
        ax1.grid(True, alpha=0.3)
        
        # 添加5日移动平均线
        daily_data['MA5'] = daily_data['sum'].rolling(window=5).mean()
        ax1.plot(daily_data['日期'], daily_data['MA5']/1e6, 
                 'r--', linewidth=2, label='5日移动平均')
        ax1.legend()
        
        # 下图：日用电波动范围
        ax2.fill_between(daily_data['日期'], daily_data['min']/1e4, daily_data['max']/1e4, 
                        alpha=0.3, color='#A23B72', label='波动范围')
        ax2.plot(daily_data['日期'], daily_data['mean']/1e4, 
                 marker='s', linewidth=2, markersize=4, color='#A23B72', label='日平均负荷')
        ax2.set_title(f'{selected_metric_col} - 日用电负荷波动分析', fontsize=14, fontweight='bold')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('用电量 (万单位)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        plt.setp(ax2.get_xticklabels(), rotation=45)
        
        st.pyplot(fig9, use_container_width=True)
    
    elif time_granularity == '星期':
        # 星期趋势分析
        st.subheader("📊 星期用电模式分析")
        
        # 按星期聚合
        weekday_data = filtered_df.groupby('星期中文')[metric_col].agg(['sum', 'mean', 'max']).reset_index()
        # 确保星期顺序
        weekday_order = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        weekday_data['星期中文'] = pd.Categorical(weekday_data['星期中文'], categories=weekday_order, ordered=True)
        weekday_data = weekday_data.sort_values('星期中文')
        
        fig10, ax = plt.subplots(figsize=(14, 8))
        
        # 绘制柱状图
        bars = ax.bar(weekday_data['星期中文'], weekday_data['sum']/1e6, 
                      color='#2E86AB', alpha=0.8)
        
        # 添加数值标签
        for bar, sum_val, mean_val in zip(bars, weekday_data['sum']/1e6, weekday_data['mean']/1e4):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'总量: {sum_val:.1f}百万\n均值: {mean_val:.1f}万',
                    ha='center', va='bottom', fontweight='bold')
        
        ax.set_title(f'{selected_metric_col} - 各星期用电总量对比', fontsize=14, fontweight='bold')
        ax.set_xlabel('星期')
        ax.set_ylabel('总用电量 (百万单位)')
        ax.grid(True, alpha=0.3, axis='y')
        
        st.pyplot(fig10, use_container_width=True)
        
        # 星期+小时热力图
        st.markdown("---")
        st.subheader("🌡️ 星期-小时用电热力图")
        
        # 按星期和小时聚合
        heatmap_data = filtered_df.groupby(['星期中文', '小时'])[metric_col].mean().reset_index()
        heatmap_data['星期中文'] = pd.Categorical(heatmap_data['星期中文'], categories=weekday_order, ordered=True)
        heatmap_data = heatmap_data.sort_values(['星期中文', '小时'])
        
        # 创建透视表
        pivot_data = heatmap_data.pivot(index='小时', columns='星期中文', values=metric_col)
        
        fig11, ax = plt.subplots(figsize=(14, 10))
        
        im = ax.imshow(pivot_data.values, cmap='YlOrRd', aspect='auto')
        
        # 设置坐标轴
        ax.set_xticks(range(len(pivot_data.columns)))
        ax.set_xticklabels(pivot_data.columns)
        ax.set_yticks(range(len(pivot_data.index)))
        ax.set_yticklabels([f'{h}:00' for h in pivot_data.index])
        
        ax.set_xlabel('星期', fontsize=12)
        ax.set_ylabel('小时', fontsize=12)
        ax.set_title(f'{selected_metric_col} - 星期-小时用电热力图', fontsize=14, fontweight='bold')
        
        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('平均用电量 (单位)', rotation=270, labelpad=20)
        
        # 在每个格子上添加数值
        for i in range(len(pivot_data.index)):
            for j in range(len(pivot_data.columns)):
                if not np.isnan(pivot_data.values[i, j]):
                    text = ax.text(j, i, f'{pivot_data.values[i, j]/1e4:.1f}万',
                                   ha="center", va="center", 
                                   color="white" if pivot_data.values[i, j] > pivot_data.values.mean() else "black",
                                   fontsize=8, fontweight='bold')
        
        st.pyplot(fig11, use_container_width=True)
    
    elif time_granularity == '时段':
        # 时段分析（早、中、晚、夜）
        st.subheader("📊 时段用电模式分析")
        
        # 定义时段
        def get_time_period(hour):
            if 6 <= hour < 12:
                return '上午 (6-12点)'
            elif 12 <= hour < 18:
                return '下午 (12-18点)'
            elif 18 <= hour < 24:
                return '晚上 (18-24点)'
            else:
                return '凌晨 (0-6点)'
        
        filtered_df['时段'] = filtered_df['小时'].apply(get_time_period)
        
        # 时段顺序
        period_order = ['凌晨 (0-6点)', '上午 (6-12点)', '下午 (12-18点)', '晚上 (18-24点)']
        
        # 按时段聚合
        period_data = filtered_df.groupby('时段')[metric_col].agg(['sum', 'mean', 'count']).reset_index()
        period_data['时段'] = pd.Categorical(period_data['时段'], categories=period_order, ordered=True)
        period_data = period_data.sort_values('时段')
        
        fig12, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 左侧：时段用电量饼图
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
        wedges, texts, autotexts = ax1.pie(period_data['sum'], labels=period_data['时段'], 
                                           autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title(f'{selected_metric_col} - 各时段用电占比', fontsize=14, fontweight='bold')
        
        # 美化饼图文字
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # 右侧：时段平均用电量柱状图
        bars = ax2.bar(period_data['时段'], period_data['mean']/1e4, color=colors)
        
        # 添加数值标签
        for bar, mean_val, count in zip(bars, period_data['mean']/1e4, period_data['count']):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{mean_val:.1f}万\n({count}个数据点)',
                    ha='center', va='bottom', fontweight='bold')
        
        ax2.set_title(f'{selected_metric_col} - 各时段平均用电量', fontsize=14, fontweight='bold')
        ax2.set_xlabel('时段')
        ax2.set_ylabel('平均用电量 (万单位)')
        ax2.grid(True, alpha=0.3, axis='y')
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        st.pyplot(fig12, use_container_width=True)

# ----------------------
# 7. 原始数据查看
# ----------------------
elif selected_page == "原始数据查看":
    st.title("📋 原始数据查看与导出")
    st.markdown("---")
    
    # 数据筛选选项
    st.subheader("🔍 数据筛选")
    
    col1, col2, col3 = st.columns(3)
    
    # 小时筛选
    hour_options = sorted(filtered_df['小时'].unique())
    selected_hours = col1.multiselect(
        "选择小时",
        options=hour_options,
        default=hour_options
    )
    
    # 星期筛选
    week_options = sorted(filtered_df['星期中文'].unique())
    selected_weeks = col2.multiselect(
        "选择星期",
        options=week_options,
        default=week_options
    )
    
    # 是否周末筛选
    weekend_options = ['全部', '工作日', '周末']
    selected_weekend = col3.selectbox(
        "选择工作日/周末",
        options=weekend_options,
        index=0
    )
    
    # 应用筛选
    filtered_data = filtered_df[
        (filtered_df['小时'].isin(selected_hours)) &
        (filtered_df['星期中文'].isin(selected_weeks))
    ].copy()
    
    # 工作日/周末筛选
    if selected_weekend == '工作日':
        filtered_data = filtered_data[filtered_data['是否周末'] == 0]
    elif selected_weekend == '周末':
        filtered_data = filtered_data[filtered_data['是否周末'] == 1]
    
    # 显示数据基本信息
    st.markdown(f"### 筛选结果：共 {len(filtered_data):,} 条记录")
    
    # 选择要显示的列
    st.subheader("📝 选择要显示的列")
    
    # 列分类
    column_categories = {
        '基本信息': ['timestamp', '日期', '小时', '星期', '星期中文', '是否周末', '是否节假日'],
        '区域用电': [col for col in area_columns if col in filtered_df.columns],
        '产业用电': [col for col in industry_columns if col in filtered_df.columns],
        '气象数据': [col for col in weather_columns if col in filtered_df.columns]
    }
    
    # 选择列分类
    selected_categories = st.multiselect(
        "选择列分类",
        options=list(column_categories.keys()),
        default=['基本信息', '区域用电', '产业用电']
    )
    
    # 收集选中的列
    selected_columns = []
    for category in selected_categories:
        selected_columns.extend(column_categories[category])
    
    # 去重并确保列存在
    selected_columns = list(set(selected_columns) & set(filtered_data.columns))
    
    if not selected_columns:
        st.warning("请至少选择一个列分类")
    else:
        # 显示数据表格
        st.dataframe(filtered_data[selected_columns], use_container_width=True, height=600)
        
        # 数据导出功能
        st.markdown("---")
        st.subheader("💾 数据导出")
        
        # 准备导出数据
        export_data = filtered_data[selected_columns].copy()
        
        # 转换日期格式为字符串
        if 'timestamp' in export_data.columns:
            export_data['timestamp'] = export_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        if '日期' in export_data.columns:
            export_data['日期'] = export_data['日期'].astype(str)
        
        # 生成CSV文件
        csv_data = export_data.to_csv(index=False, encoding='utf-8-sig')
        
        # 下载按钮
        st.download_button(
            label="导出筛选数据为CSV文件",
            data=csv_data,
            file_name=f"2023年1月用电数据_{selected_dates[0]}_to_{selected_dates[1]}.csv",
            mime="text/csv",
            key="download_csv"
        )
        
        # 数据统计摘要
        st.markdown("---")
        st.subheader("📊 数据统计摘要")
        
        # 选择数值列进行统计
        numeric_cols = export_data.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            selected_numeric_cols = st.multiselect(
                "选择要统计的数值列",
                options=numeric_cols,
                default=numeric_cols[:5] if len(numeric_cols) > 5 else numeric_cols
            )
            
            if selected_numeric_cols:
                stats_summary = export_data[selected_numeric_cols].describe()
                st.dataframe(stats_summary.round(2), use_container_width=True)
        else:
            st.info("所选列中没有数值类型的数据可统计")

# ----------------------
# 8. 页脚信息
# ----------------------
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px;">
        📊 2023年1月用电数据分析平台 | 数据更新时间: 2023年1月
        <br>
        提示: 可通过左侧边栏调整时间范围和分析参数
    </div>
""", unsafe_allow_html=True)
