"""
STF Digital Twin - Historical Analytics Page
Time-series visualization for telemetry data, energy consumption, and predictive maintenance
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="STF Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Glassmorphism styling
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #0a0f1a 0%, #1a1f2e 50%, #0d1117 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Glass card effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* Metric cards */
    .metric-card {
        background: rgba(0, 210, 190, 0.08);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 210, 190, 0.2);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #00d2be;
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 8px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    .page-title {
        font-size: 2rem;
        background: linear-gradient(135deg, #00d2be 0%, #00a896 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    .page-subtitle {
        color: rgba(255, 255, 255, 0.5);
        font-size: 1rem;
        margin-bottom: 32px;
    }
    
    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: rgba(10, 15, 26, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Chart containers */
    .chart-container {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #00d2be 0%, #00a896 100%);
        color: #0a0f1a;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 210, 190, 0.3);
    }
    
    /* Select box styling */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
    }
    
    /* Date input styling */
    .stDateInput > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: rgba(255, 255, 255, 0.6);
        border-radius: 8px;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(0, 210, 190, 0.2);
        color: #00d2be;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_URL = "http://localhost:8000"


def generate_sample_telemetry_data(days: int = 7) -> pd.DataFrame:
    """Generate sample telemetry data for demonstration"""
    np.random.seed(42)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Generate timestamps
    timestamps = pd.date_range(start=start_date, end=end_date, freq='5min')
    
    data = []
    for ts in timestamps:
        # Simulate daily patterns
        hour = ts.hour
        day_factor = 1.0 if ts.weekday() < 5 else 0.3  # Lower on weekends
        
        # Peak hours: 9-12 and 14-17
        if 9 <= hour <= 12 or 14 <= hour <= 17:
            activity_factor = 1.0
        elif 6 <= hour <= 9 or 17 <= hour <= 20:
            activity_factor = 0.6
        else:
            activity_factor = 0.2
        
        base_activity = day_factor * activity_factor
        
        # HBW metrics
        data.append({
            'timestamp': ts,
            'device_id': 'HBW',
            'metric': 'position_x',
            'value': np.random.uniform(50, 350) * base_activity + 100,
            'unit': 'mm'
        })
        data.append({
            'timestamp': ts,
            'device_id': 'HBW',
            'metric': 'energy',
            'value': np.random.uniform(20, 80) * base_activity + 10,
            'unit': 'W'
        })
        data.append({
            'timestamp': ts,
            'device_id': 'HBW',
            'metric': 'operations',
            'value': int(np.random.poisson(5) * base_activity),
            'unit': 'count'
        })
        
        # VGR metrics
        data.append({
            'timestamp': ts,
            'device_id': 'VGR',
            'metric': 'energy',
            'value': np.random.uniform(15, 60) * base_activity + 8,
            'unit': 'W'
        })
        
        # Conveyor metrics
        data.append({
            'timestamp': ts,
            'device_id': 'CONVEYOR',
            'metric': 'energy',
            'value': np.random.uniform(10, 40) * base_activity + 5,
            'unit': 'W'
        })
    
    return pd.DataFrame(data)


def generate_sample_energy_data(days: int = 30) -> pd.DataFrame:
    """Generate sample energy consumption data"""
    np.random.seed(42)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    timestamps = pd.date_range(start=start_date, end=end_date, freq='1h')
    
    data = []
    for ts in timestamps:
        hour = ts.hour
        day_factor = 1.0 if ts.weekday() < 5 else 0.4
        
        # Peak hours pattern
        if 9 <= hour <= 17:
            peak_factor = 1.0
        elif 6 <= hour <= 9 or 17 <= hour <= 21:
            peak_factor = 0.6
        else:
            peak_factor = 0.2
        
        base_energy = day_factor * peak_factor
        
        for device in ['HBW', 'VGR', 'CONVEYOR']:
            device_factor = {'HBW': 1.0, 'VGR': 0.7, 'CONVEYOR': 0.5}[device]
            
            data.append({
                'timestamp': ts,
                'device_id': device,
                'joules': np.random.uniform(500, 2000) * base_energy * device_factor,
                'voltage': 24.0 + np.random.uniform(-0.5, 0.5),
                'current': np.random.uniform(1, 5) * base_energy * device_factor
            })
    
    return pd.DataFrame(data)


def generate_sample_production_data(days: int = 30) -> pd.DataFrame:
    """Generate sample production throughput data"""
    np.random.seed(42)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='1D')
    
    data = []
    for date in dates:
        day_factor = 1.0 if date.weekday() < 5 else 0.3
        
        data.append({
            'date': date.date(),
            'store_operations': int(np.random.poisson(50) * day_factor),
            'retrieve_operations': int(np.random.poisson(45) * day_factor),
            'total_cookies': int(np.random.poisson(95) * day_factor),
            'avg_cycle_time': np.random.uniform(15, 25),
            'uptime_percent': np.random.uniform(92, 99.5) if day_factor > 0.5 else np.random.uniform(70, 85)
        })
    
    return pd.DataFrame(data)


def fetch_api_data(endpoint: str):
    """Fetch data from API"""
    try:
        response = requests.get(f"{API_URL}/{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


# Sidebar
with st.sidebar:
    st.markdown("### 📊 Analytics Settings")
    st.markdown("---")
    
    # Date range selection
    st.markdown("**Date Range**")
    date_range = st.selectbox(
        "Select period",
        ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"],
        index=1
    )
    
    if date_range == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start", datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("End", datetime.now())
        days = (end_date - start_date).days
    else:
        days_map = {
            "Last 24 Hours": 1,
            "Last 7 Days": 7,
            "Last 30 Days": 30,
            "Last 90 Days": 90
        }
        days = days_map.get(date_range, 7)
    
    st.markdown("---")
    
    # Device filter
    st.markdown("**Device Filter**")
    devices = st.multiselect(
        "Select devices",
        ["HBW", "VGR", "CONVEYOR"],
        default=["HBW", "VGR", "CONVEYOR"]
    )
    
    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    
    # Navigation
    st.markdown("**Navigation**")
    if st.button("← Back to Dashboard", use_container_width=True):
        st.switch_page("app.py")


# Main content
st.markdown('<h1 class="page-title">Historical Analytics</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-subtitle">Time-series visualization and predictive insights</p>', unsafe_allow_html=True)

# Generate sample data
telemetry_df = generate_sample_telemetry_data(days)
energy_df = generate_sample_energy_data(days)
production_df = generate_sample_production_data(days)

# Filter by devices
telemetry_df = telemetry_df[telemetry_df['device_id'].isin(devices)]
energy_df = energy_df[energy_df['device_id'].isin(devices)]

# KPI Summary Cards
st.markdown("### 📈 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_energy = energy_df['joules'].sum() / 1000  # Convert to kJ
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{total_energy:,.0f}</p>
        <p class="metric-label">Total Energy (kJ)</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    total_operations = production_df['total_cookies'].sum()
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{total_operations:,}</p>
        <p class="metric-label">Total Operations</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    avg_uptime = production_df['uptime_percent'].mean()
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{avg_uptime:.1f}%</p>
        <p class="metric-label">Avg Uptime</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    avg_cycle = production_df['avg_cycle_time'].mean()
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{avg_cycle:.1f}s</p>
        <p class="metric-label">Avg Cycle Time</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tabs for different analytics views
tab1, tab2, tab3, tab4 = st.tabs(["⚡ Energy Analysis", "🏭 Production Metrics", "🔧 Hardware Utilization", "🔮 Predictive Insights"])

with tab1:
    st.markdown("### Energy Consumption Over Time")
    
    # Aggregate energy by hour and device
    energy_hourly = energy_df.groupby([pd.Grouper(key='timestamp', freq='1h'), 'device_id'])['joules'].sum().reset_index()
    
    fig_energy = px.area(
        energy_hourly,
        x='timestamp',
        y='joules',
        color='device_id',
        title='Energy Consumption by Device',
        color_discrete_map={'HBW': '#00d2be', 'VGR': '#ff6b6b', 'CONVEYOR': '#ffd93d'}
    )
    fig_energy.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='rgba(255,255,255,0.8)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Energy (Joules)')
    )
    st.plotly_chart(fig_energy, use_container_width=True)
    
    # Energy distribution pie chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Energy Distribution by Device")
        energy_by_device = energy_df.groupby('device_id')['joules'].sum().reset_index()
        
        fig_pie = px.pie(
            energy_by_device,
            values='joules',
            names='device_id',
            color='device_id',
            color_discrete_map={'HBW': '#00d2be', 'VGR': '#ff6b6b', 'CONVEYOR': '#ffd93d'},
            hole=0.4
        )
        fig_pie.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='rgba(255,255,255,0.8)'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.markdown("#### Hourly Energy Pattern")
        energy_df['hour'] = energy_df['timestamp'].dt.hour
        hourly_pattern = energy_df.groupby('hour')['joules'].mean().reset_index()
        
        fig_hourly = px.bar(
            hourly_pattern,
            x='hour',
            y='joules',
            title='Average Energy by Hour of Day',
            color='joules',
            color_continuous_scale=['#0a0f1a', '#00d2be']
        )
        fig_hourly.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='rgba(255,255,255,0.8)',
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Hour'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Avg Energy (J)'),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_hourly, use_container_width=True)

with tab2:
    st.markdown("### Production Throughput")
    
    # Daily operations chart
    fig_ops = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig_ops.add_trace(
        go.Bar(
            x=production_df['date'],
            y=production_df['store_operations'],
            name='Store Operations',
            marker_color='#00d2be'
        ),
        secondary_y=False
    )
    
    fig_ops.add_trace(
        go.Bar(
            x=production_df['date'],
            y=production_df['retrieve_operations'],
            name='Retrieve Operations',
            marker_color='#ff6b6b'
        ),
        secondary_y=False
    )
    
    fig_ops.add_trace(
        go.Scatter(
            x=production_df['date'],
            y=production_df['uptime_percent'],
            name='Uptime %',
            line=dict(color='#ffd93d', width=2),
            mode='lines+markers'
        ),
        secondary_y=True
    )
    
    fig_ops.update_layout(
        title='Daily Operations & Uptime',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='rgba(255,255,255,0.8)',
        barmode='group',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Operations'),
        yaxis2=dict(gridcolor='rgba(255,255,255,0.05)', title='Uptime %', range=[0, 100])
    )
    st.plotly_chart(fig_ops, use_container_width=True)
    
    # Cycle time analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Cycle Time Trend")
        fig_cycle = px.line(
            production_df,
            x='date',
            y='avg_cycle_time',
            title='Average Cycle Time',
            markers=True
        )
        fig_cycle.update_traces(line_color='#00d2be', marker_color='#00d2be')
        fig_cycle.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='rgba(255,255,255,0.8)',
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Seconds')
        )
        st.plotly_chart(fig_cycle, use_container_width=True)
    
    with col2:
        st.markdown("#### Weekly Comparison")
        production_df['weekday'] = pd.to_datetime(production_df['date']).dt.day_name()
        weekly_avg = production_df.groupby('weekday')['total_cookies'].mean().reindex([
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        ])
        
        fig_weekly = px.bar(
            x=weekly_avg.index,
            y=weekly_avg.values,
            title='Average Operations by Day of Week',
            color=weekly_avg.values,
            color_continuous_scale=['#1a1f2e', '#00d2be']
        )
        fig_weekly.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='rgba(255,255,255,0.8)',
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title=''),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Avg Operations'),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_weekly, use_container_width=True)

with tab3:
    st.markdown("### Hardware Utilization")
    
    # Position heatmap for HBW
    if 'HBW' in devices:
        st.markdown("#### HBW Position Heatmap")
        
        hbw_positions = telemetry_df[
            (telemetry_df['device_id'] == 'HBW') & 
            (telemetry_df['metric'] == 'position_x')
        ].copy()
        
        if not hbw_positions.empty:
            hbw_positions['hour'] = hbw_positions['timestamp'].dt.hour
            hbw_positions['day'] = hbw_positions['timestamp'].dt.day_name()
            
            heatmap_data = hbw_positions.pivot_table(
                values='value',
                index='day',
                columns='hour',
                aggfunc='mean'
            ).reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
            
            fig_heatmap = px.imshow(
                heatmap_data,
                title='HBW Activity Heatmap (Position X)',
                color_continuous_scale=['#0a0f1a', '#00d2be'],
                aspect='auto'
            )
            fig_heatmap.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='rgba(255,255,255,0.8)',
                xaxis_title='Hour of Day',
                yaxis_title='Day of Week'
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Device status timeline
    st.markdown("#### Device Activity Timeline")
    
    # Simulate device status over time
    status_data = []
    for device in devices:
        device_energy = energy_df[energy_df['device_id'] == device].copy()
        device_energy['status'] = device_energy['joules'].apply(
            lambda x: 'Active' if x > 500 else ('Idle' if x > 100 else 'Standby')
        )
        device_energy['device'] = device
        status_data.append(device_energy[['timestamp', 'device', 'status', 'joules']])
    
    if status_data:
        status_df = pd.concat(status_data)
        
        fig_timeline = px.scatter(
            status_df,
            x='timestamp',
            y='device',
            color='status',
            size='joules',
            title='Device Status Over Time',
            color_discrete_map={'Active': '#00d2be', 'Idle': '#ffd93d', 'Standby': '#ff6b6b'}
        )
        fig_timeline.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='rgba(255,255,255,0.8)',
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

with tab4:
    st.markdown("### Predictive Maintenance Insights")
    
    # Maintenance score calculation
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Equipment Health Score")
        
        health_scores = {
            'HBW': np.random.uniform(85, 98),
            'VGR': np.random.uniform(75, 95),
            'CONVEYOR': np.random.uniform(80, 99)
        }
        
        for device, score in health_scores.items():
            if device in devices:
                color = '#00d2be' if score >= 90 else ('#ffd93d' if score >= 75 else '#ff6b6b')
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); border-radius: 8px; padding: 16px; margin-bottom: 12px; border-left: 4px solid {color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: rgba(255,255,255,0.8); font-weight: 500;">{device}</span>
                        <span style="color: {color}; font-weight: 700; font-size: 1.5rem;">{score:.1f}%</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 8px; margin-top: 8px;">
                        <div style="background: {color}; width: {score}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Predicted Maintenance Schedule")
        
        maintenance_items = [
            {"device": "HBW", "component": "Gripper Motor", "days": 12, "priority": "Medium"},
            {"device": "VGR", "component": "Vacuum Pump", "days": 5, "priority": "High"},
            {"device": "CONVEYOR", "component": "Belt Tension", "days": 28, "priority": "Low"},
            {"device": "HBW", "component": "X-Axis Bearing", "days": 45, "priority": "Low"},
        ]
        
        for item in maintenance_items:
            if item['device'] in devices:
                priority_color = {'High': '#ff6b6b', 'Medium': '#ffd93d', 'Low': '#00d2be'}[item['priority']]
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="color: rgba(255,255,255,0.8); font-weight: 500;">{item['device']} - {item['component']}</span>
                            <span style="background: {priority_color}; color: #0a0f1a; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; margin-left: 8px;">{item['priority']}</span>
                        </div>
                        <span style="color: rgba(255,255,255,0.6);">in {item['days']} days</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Anomaly detection
    st.markdown("#### Anomaly Detection")
    
    # Generate sample anomaly data
    anomaly_times = pd.date_range(end=datetime.now(), periods=10, freq='6h')
    anomalies = pd.DataFrame({
        'timestamp': anomaly_times,
        'device': np.random.choice(devices, 10) if devices else ['HBW'] * 10,
        'metric': np.random.choice(['Energy Spike', 'Position Drift', 'Cycle Time', 'Temperature'], 10),
        'severity': np.random.choice(['Warning', 'Critical', 'Info'], 10, p=[0.5, 0.2, 0.3]),
        'value': np.random.uniform(1.5, 3.0, 10)
    })
    
    severity_colors = {'Critical': '#ff6b6b', 'Warning': '#ffd93d', 'Info': '#00d2be'}
    
    fig_anomaly = px.scatter(
        anomalies,
        x='timestamp',
        y='value',
        color='severity',
        size='value',
        hover_data=['device', 'metric'],
        title='Detected Anomalies (Standard Deviations from Normal)',
        color_discrete_map=severity_colors
    )
    fig_anomaly.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='rgba(255,255,255,0.8)',
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Deviation (σ)')
    )
    st.plotly_chart(fig_anomaly, use_container_width=True)

# Export section
st.markdown("---")
st.markdown("### 📥 Export Data")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Export Energy Data (CSV)", use_container_width=True):
        csv = energy_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"stf_energy_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("🏭 Export Production Data (CSV)", use_container_width=True):
        csv = production_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"stf_production_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col3:
    if st.button("📈 Export Telemetry Data (CSV)", use_container_width=True):
        csv = telemetry_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"stf_telemetry_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.4); font-size: 0.875rem;">
    STF Digital Twin Analytics • Data refreshed every 5 minutes • 
    <a href="/" style="color: #00d2be;">Back to Dashboard</a>
</div>
""", unsafe_allow_html=True)
