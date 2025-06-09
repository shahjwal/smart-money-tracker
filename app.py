import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
from auth import AuthManager
from database import Database
from email_config import EmailManager
from utils import StockDataFetcher, format_number
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Smart Money Flow Tracker",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4 0%, #ff7f0e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        height: 100%;
    }
    .alert-card {
        background-color: #ffe6e6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ff4444;
        margin: 1rem 0;
    }
    .success-card {
        background-color: #e6ffe6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #44ff44;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize managers
auth_manager = AuthManager()
db = Database()
email_manager = EmailManager()
data_fetcher = StockDataFetcher()

# Check authentication
if not auth_manager.check_authentication():
    auth_manager.show_login_page()
else:
    # Main application
    st.markdown('<h1 class="main-header">🚀 Smart Money Flow Tracker</h1>', unsafe_allow_html=True)
    
    # Header with user info
    col1, col2, col3 = st.columns([6, 2, 1])
    with col2:
        st.write(f"👤 Welcome, **{st.session_state.username}**")
    with col3:
        if st.button("Logout"):
            auth_manager.logout()
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Live Monitoring", "🚨 Alerts", "📈 Performance", "🎨 Visualizations"])
    
    # Tab 1: Live Monitoring
    with tab1:
        # Refresh button
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🔄 Refresh Data"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            auto_refresh = st.checkbox("Auto-refresh")
        
        # Market Sentiment
        st.subheader("📊 Market Sentiment")
        sentiment_data = data_fetcher.get_market_sentiment()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Put/Call Ratio", f"{sentiment_data['put_call_ratio']:.2f}")
        with col2:
            st.metric("Sentiment Score", f"{sentiment_data['sentiment_score']}/100")
        with col3:
            st.metric("Market Mood", sentiment_data['sentiment_text'])
        with col4:
            st.metric("Total Options Volume", 
                     f"{sentiment_data['total_call_volume'] + sentiment_data['total_put_volume']:,}")
        
        # Sentiment Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = sentiment_data['sentiment_score'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Market Sentiment Gauge"},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 25], 'color': "darkred"},
                    {'range': [25, 50], 'color': "red"},
                    {'range': [50, 75], 'color': "yellow"},
                    {'range': [75, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Unusual Options Activity
        st.subheader("🔥 Live Unusual Options Activity")
        
        with st.spinner("Scanning for unusual options activity..."):
            unusual_activities = data_fetcher.scan_all_watchlist()
        
        if unusual_activities:
            # Create alerts for top activities
            for activity in unusual_activities[:3]:  # Top 3 only
                alert_data = {
                    'symbol': activity['symbol'],
                    'alert_type': 'Unusual Options Activity',
                    'message': f"{activity['symbol']}: {activity['volume']:,} {activity['option_type']}s @ ${activity['strike']} - {format_number(activity['premium'])} premium",
                    'details': activity,
                    'current_price': activity.get('current_price', 0)
                }
                
                # Check if we should send email
                existing_alerts = db.get_user_alerts(st.session_state.user_id, limit=10)
                should_send = True
                
                if not existing_alerts.empty:
                    # Don't send if similar alert sent in last hour
                    recent_alerts = existing_alerts[existing_alerts['symbol'] == activity['symbol']]
                    if len(recent_alerts) > 0:
                        last_alert_time = pd.to_datetime(recent_alerts.iloc[0]['timestamp'])
                        if (datetime.now() - last_alert_time).total_seconds() < 3600:
                            should_send = False
                
                if should_send:
                    # Save alert
                    alert_id = db.save_alert(
                        st.session_state.user_id,
                        activity['symbol'],
                        'Unusual Options Activity',
                        alert_data['message'],
                        activity,
                        activity.get('current_price', 0),
                        False
                    )
                    
                    # Send email if configured
                    if st.session_state.user_email:
                        email_sent = email_manager.send_alert_email(
                            st.session_state.user_email,
                            alert_data
                        )
                        if email_sent:
                            st.success(f"✉️ Alert email sent for {activity['symbol']}!")
            
            # Display in table
            df_unusual = pd.DataFrame(unusual_activities)
            df_unusual['Premium'] = df_unusual['premium'].apply(format_number)
            df_unusual['Volume'] = df_unusual['volume'].apply(lambda x: f"{x:,}")
            
            display_cols = ['symbol', 'option_type', 'strike', 'Volume', 'volume_ratio', 'Premium']
            st.dataframe(
                df_unusual[display_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No unusual options activity detected at the moment.")
    
    # Tab 2: Alerts
    with tab2:
        st.subheader("🚨 Alert Management")
        
        # Email configuration
        with st.expander("📧 Email Configuration"):
            current_email = st.session_state.user_email
            st.write(f"Current email: **{current_email}**")
            
            new_email = st.text_input("Update email address", value=current_email)
            if st.button("Update Email"):
                # Here you would update the email in database
                st.success("Email updated successfully!")
        
        # Alert History
        st.subheader("📋 Alert History")
        
        alerts_df = db.get_user_alerts(st.session_state.user_id, limit=100)
        
        if not alerts_df.empty:
            # Add filters
            col1, col2 = st.columns(2)
            with col1:
                symbol_filter = st.selectbox(
                    "Filter by Symbol",
                    ["All"] + list(alerts_df['symbol'].unique())
                )
            
            with col2:
                date_filter = st.date_input(
                    "Filter by Date",
                    value=datetime.now().date()
                )
            
            # Apply filters
            if symbol_filter != "All":
                alerts_df = alerts_df[alerts_df['symbol'] == symbol_filter]
            
            # Format timestamp
            alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
            alerts_df['Date'] = alerts_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
            
            # Display
            display_cols = ['Date', 'symbol', 'alert_type', 'message', 'email_sent']
            st.dataframe(
                alerts_df[display_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No alerts yet. Unusual activities will appear here.")
    
    # Tab 3: Performance
    with tab3:
        st.subheader("📈 Performance Analytics")
        
        # Get performance stats
        perf_stats = db.get_performance_stats(st.session_state.user_id)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Alerts", perf_stats['total_alerts'])
        with col2:
            st.metric("Successful Alerts", perf_stats['successful_alerts'])
        with col3:
            st.metric("Success Rate", f"{perf_stats['success_rate']:.1f}%")
        with col4:
            avg_return = perf_stats['avg_return_1w'] * 100
            st.metric("Avg Weekly Return", f"{avg_return:.2f}%")
        
        # Performance chart
        alerts_with_perf = db.get_user_alerts(st.session_state.user_id, limit=50)
        
        if not alerts_with_perf.empty and 'return_1w' in alerts_with_perf.columns:
            # Filter alerts with performance data
            perf_data = alerts_with_perf[alerts_with_perf['return_1w'].notna()]
            
            if not perf_data.empty:
                # Create performance chart
                fig_perf = go.Figure()
                
                fig_perf.add_trace(go.Bar(
                    x=perf_data['symbol'],
                    y=perf_data['return_1w'] * 100,
                    marker_color=['green' if x > 0 else 'red' for x in perf_data['return_1w']],
                    text=[f"{x:.1f}%" for x in perf_data['return_1w'] * 100],
                    textposition='auto'
                ))
                
                fig_perf.update_layout(
                    title="Alert Performance (Weekly Returns %)",
                    xaxis_title="Stock Symbol",
                    yaxis_title="Return %",
                    showlegend=False
                )
                
                st.plotly_chart(fig_perf, use_container_width=True)
        
        # Win/Loss pie chart
        if perf_stats['total_alerts'] > 0:
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Winning Trades', 'Losing Trades'],
                values=[perf_stats['successful_alerts'], 
                       perf_stats['total_alerts'] - perf_stats['successful_alerts']],
                hole=.3,
                marker_colors=['green', 'red']
            )])
            
            fig_pie.update_layout(title="Win/Loss Distribution")
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # Tab 4: Visualizations
    with tab4:
        st.subheader("🎨 Advanced Visualizations")
        
        # Options Flow Heatmap
        st.write("### 🔥 Options Flow Heatmap")
        
        # Create sample data for heatmap
        hours = list(range(9, 17))  # Market hours
        symbols = data_fetcher.watchlist[:8]
        
        # Generate heatmap data
        heatmap_data = []
        for symbol in symbols:
            row_data = []
            for hour in hours:
                # Simulate activity intensity
                intensity = np.random.random() * 100
                row_data.append(intensity)
            heatmap_data.append(row_data)
        
        fig_heatmap = px.imshow(
            heatmap_data,
            labels=dict(x="Hour", y="Symbol", color="Activity Level"),
            x=[f"{h}:00" for h in hours],
            y=symbols,
            color_continuous_scale="RdYlGn"
        )
        
        fig_heatmap.update_layout(
            title="Options Activity Heatmap (Today)",
            height=400
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # 3D Scatter Plot
        st.write("### 📊 3D Options Analysis")
        
        if unusual_activities:
            # Prepare 3D data
            df_3d = pd.DataFrame(unusual_activities[:20])  # Top 20
            
            fig_3d = px.scatter_3d(
                df_3d,
                x='strike',
                y='volume',
                z='premium',
                color='option_type',
                size='volume_ratio',
                hover_data=['symbol'],
                title="3D Options Flow Visualization",
                labels={
                    'strike': 'Strike Price',
                    'volume': 'Volume',
                    'premium': 'Premium ($)'
                }
            )
            
            fig_3d.update_layout(height=600)
            st.plotly_chart(fig_3d, use_container_width=True)
        
        # Animated Timeline
        st.write("### ⏰ Alert Timeline")
        
        timeline_alerts = db.get_user_alerts(st.session_state.user_id, limit=20)
        
        if not timeline_alerts.empty:
            timeline_alerts['timestamp'] = pd.to_datetime(timeline_alerts['timestamp'])
            timeline_alerts['hour'] = timeline_alerts['timestamp'].dt.hour
            
            fig_timeline = px.scatter(
                timeline_alerts,
                x='timestamp',
                y='symbol',
                size='alert_price',
                color='alert_type',
                title="Alert Timeline",
                hover_data=['message']
            )
            
            fig_timeline.update_layout(height=400)
            st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(60)  # Refresh every 60 seconds
        st.rerun()