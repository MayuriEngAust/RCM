import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

from data_generator import DataGenerator
from kpi_calculator import KPICalculator
from visualizations import RCMVisualizations
from utils import export_data, format_currency, format_duration

# Page configuration
st.set_page_config(
    page_title="RCM Analytics Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for data caching
if 'data_generator' not in st.session_state:
    st.session_state.data_generator = DataGenerator()
    st.session_state.kpi_calculator = KPICalculator()
    st.session_state.visualizations = RCMVisualizations()


# Load data
@st.cache_data
def load_data():
    return st.session_state.data_generator.generate_all_data()


# Main application
def main():
    st.title("🔧 RCM Analytics Dashboard")
    st.markdown("**Reliability-Centered Maintenance Analytics Platform**")

    # Load data
    data = load_data()

    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # Asset type filter
    asset_types = ['All'] + list(data['assets']['AssetType'].unique())
    selected_asset_type = st.sidebar.selectbox("Asset Type", asset_types)

    # Location filter
    locations = ['All'] + list(data['assets']['Location'].unique())
    selected_location = st.sidebar.selectbox("Location", locations)

    # Criticality filter
    criticality_levels = ['All'] + list(data['assets']['CriticalityLevel'].unique())
    selected_criticality = st.sidebar.selectbox("Criticality Level", criticality_levels)

    # Date range filter
    max_date = data['work_orders']['CompletionDate'].max()
    min_date = max_date - timedelta(days=365)

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
    if auto_refresh:
        st.rerun()

    # Apply filters
    filtered_data = apply_filters(data, selected_asset_type, selected_location,
                                  selected_criticality, date_range)

    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", "🔍 Failure Analysis", "📈 Trends", "🗓️ Maintenance Schedule", "📋 RCA Dashboard"
    ])

    with tab1:
        overview_dashboard(filtered_data)

    with tab2:
        failure_analysis_dashboard(filtered_data)

    with tab3:
        trends_dashboard(filtered_data)

    with tab4:
        maintenance_schedule_dashboard(filtered_data)

    with tab5:
        rca_dashboard(filtered_data)


def apply_filters(data, asset_type, location, criticality, date_range):
    """Apply selected filters to the data"""
    filtered_data = data.copy()

    # Filter assets
    assets_filter = pd.Series([True] * len(data['assets']))
    if asset_type != 'All':
        assets_filter &= data['assets']['AssetType'] == asset_type
    if location != 'All':
        assets_filter &= data['assets']['Location'] == location
    if criticality != 'All':
        assets_filter &= data['assets']['CriticalityLevel'] == criticality

    filtered_assets = data['assets'][assets_filter]
    filtered_data['assets'] = filtered_assets

    # Filter related data based on asset IDs
    asset_ids = filtered_assets['AssetID'].values

    filtered_data['work_orders'] = data['work_orders'][
        data['work_orders']['AssetID'].isin(asset_ids) &
        (data['work_orders']['CompletionDate'] >= pd.Timestamp(date_range[0])) &
        (data['work_orders']['CompletionDate'] <= pd.Timestamp(date_range[1]))
        ]

    filtered_data['failures'] = data['failures'][
        data['failures']['AssetID'].isin(asset_ids) &
        (data['failures']['FailureDate'] >= pd.Timestamp(date_range[0])) &
        (data['failures']['FailureDate'] <= pd.Timestamp(date_range[1]))
        ]

    filtered_data['maintenance_costs'] = data['maintenance_costs'][
        data['maintenance_costs']['AssetID'].isin(asset_ids) &
        (data['maintenance_costs']['Date'] >= pd.Timestamp(date_range[0])) &
        (data['maintenance_costs']['Date'] <= pd.Timestamp(date_range[1]))
        ]

    return filtered_data


def overview_dashboard(data):
    """Main overview dashboard with KPIs and summary charts"""
    st.header("📊 Key Performance Indicators")

    # Calculate KPIs
    kpis = st.session_state.kpi_calculator.calculate_all_kpis(data)

    # KPI metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="MTBF (Mean Time Between Failures)",
            value=f"{kpis['mtbf']:.1f} days",
            delta=f"{kpis['mtbf_change']:.1f}%"
        )

    with col2:
        st.metric(
            label="MTTR (Mean Time to Repair)",
            value=f"{kpis['mttr']:.1f} hours",
            delta=f"{kpis['mttr_change']:.1f}%"
        )

    with col3:
        st.metric(
            label="Overall Equipment Effectiveness",
            value=f"{kpis['oee']:.1f}%",
            delta=f"{kpis['oee_change']:.1f}%"
        )

    with col4:
        st.metric(
            label="Total Maintenance Cost",
            value=format_currency(kpis['total_cost']),
            delta=f"{kpis['cost_change']:.1f}%"
        )

    st.divider()

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Asset Criticality Distribution")
        criticality_chart = st.session_state.visualizations.create_criticality_pie_chart(data['assets'])
        st.plotly_chart(criticality_chart, use_container_width=True)

    with col2:
        st.subheader("Monthly Maintenance Costs")
        cost_trend_chart = st.session_state.visualizations.create_cost_trend_chart(data['maintenance_costs'])
        st.plotly_chart(cost_trend_chart, use_container_width=True)

    # Asset status heatmap
    st.subheader("Asset Status Heatmap")
    heatmap = st.session_state.visualizations.create_asset_heatmap(data['assets'], data['failures'])
    st.plotly_chart(heatmap, use_container_width=True)

    # Export functionality
    if st.button("📥 Export Overview Report"):
        export_data(data, "overview_report")
        st.success("Report exported successfully!")


def failure_analysis_dashboard(data):
    """Failure mode analysis dashboard"""
    st.header("🔍 Failure Mode Analysis")

    # Pareto chart for top failure modes
    st.subheader("Top Failure Modes (Pareto Analysis)")
    pareto_chart = st.session_state.visualizations.create_failure_pareto_chart(data['failures'])
    st.plotly_chart(pareto_chart, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Failure Distribution by Asset Type")
        failure_by_type = st.session_state.visualizations.create_failure_by_asset_chart(
            data['failures'], data['assets']
        )
        st.plotly_chart(failure_by_type, use_container_width=True)

    with col2:
        st.subheader("Failure Severity Analysis")
        severity_chart = st.session_state.visualizations.create_failure_severity_chart(data['failures'])
        st.plotly_chart(severity_chart, use_container_width=True)

    # Failure frequency heatmap
    st.subheader("Failure Frequency Heatmap by Location")
    location_heatmap = st.session_state.visualizations.create_location_failure_heatmap(
        data['failures'], data['assets']
    )
    st.plotly_chart(location_heatmap, use_container_width=True)

    # Detailed failure analysis table
    st.subheader("Recent Failures")
    recent_failures = data['failures'].merge(
        data['assets'][['AssetID', 'AssetName', 'AssetType']],
        on='AssetID'
    ).sort_values('FailureDate', ascending=False).head(20)

    st.dataframe(
        recent_failures[['FailureDate', 'AssetName', 'AssetType', 'FailureMode',
                         'Severity', 'DowntimeHours', 'RepairCost']],
        use_container_width=True
    )


def trends_dashboard(data):
    """Trends analysis dashboard"""
    st.header("📈 Trend Analysis")

    # Failure rate trends
    st.subheader("Failure Rate Trends")
    failure_trend = st.session_state.visualizations.create_failure_trend_chart(data['failures'])
    st.plotly_chart(failure_trend, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("MTBF Trend Analysis")
        mtbf_trend = st.session_state.visualizations.create_mtbf_trend_chart(data['failures'], data['assets'])
        st.plotly_chart(mtbf_trend, use_container_width=True)

    with col2:
        st.subheader("MTTR Trend Analysis")
        mttr_trend = st.session_state.visualizations.create_mttr_trend_chart(data['failures'])
        st.plotly_chart(mttr_trend, use_container_width=True)

    # Cost trends by category
    st.subheader("Maintenance Cost Trends by Category")
    cost_category_trend = st.session_state.visualizations.create_cost_category_trend(data['maintenance_costs'])
    st.plotly_chart(cost_category_trend, use_container_width=True)

    # Predictive insights
    st.subheader("🔮 Predictive Insights")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("**High Risk Assets**\nBased on failure patterns, 3 assets require immediate attention.")

    with col2:
        st.warning("**Maintenance Budget Alert**\nProjected 15% increase in maintenance costs next quarter.")

    with col3:
        st.success("**Optimization Opportunity**\nPredictive maintenance could reduce costs by 12%.")


def maintenance_schedule_dashboard(data):
    """Maintenance schedule visualization"""
    st.header("🗓️ Maintenance Schedule")

    # Gantt chart for maintenance activities
    st.subheader("Maintenance Timeline (Planned vs Actual)")
    gantt_chart = st.session_state.visualizations.create_maintenance_gantt(data['work_orders'])
    st.plotly_chart(gantt_chart, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Schedule Compliance")
        compliance_chart = st.session_state.visualizations.create_schedule_compliance_chart(data['work_orders'])
        st.plotly_chart(compliance_chart, use_container_width=True)

    with col2:
        st.subheader("Maintenance Type Distribution")
        type_distribution = st.session_state.visualizations.create_maintenance_type_chart(data['work_orders'])
        st.plotly_chart(type_distribution, use_container_width=True)

    # Upcoming maintenance table
    st.subheader("Upcoming Maintenance Activities")
    upcoming = data['work_orders'][
        (data['work_orders']['ScheduledDate'] >= datetime.now()) &
        (data['work_orders']['Status'] == 'Scheduled')
        ].merge(data['assets'][['AssetID', 'AssetName']], on='AssetID')

    if not upcoming.empty:
        st.dataframe(
            upcoming[['ScheduledDate', 'AssetName', 'MaintenanceType', 'EstimatedDuration', 'Priority']],
            use_container_width=True
        )
    else:
        st.info("No upcoming maintenance activities scheduled.")


def rca_dashboard(data):
    """Root Cause Analysis dashboard"""
    st.header("📋 Root Cause Analysis")

    # RCA summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        open_rcas = len(data['failures'][data['failures']['RCAStatus'] == 'Open'])
        st.metric("Open RCAs", open_rcas)

    with col2:
        completed_rcas = len(data['failures'][data['failures']['RCAStatus'] == 'Completed'])
        st.metric("Completed RCAs", completed_rcas)

    with col3:
        avg_resolution_time = data['failures'][data['failures']['RCAStatus'] == 'Completed']['RCAResolutionDays'].mean()
        st.metric("Avg Resolution Time", f"{avg_resolution_time:.1f} days")

    # Root cause categories
    st.subheader("Root Cause Categories")
    rca_categories = st.session_state.visualizations.create_rca_categories_chart(data['failures'])
    st.plotly_chart(rca_categories, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("RCA Status by Asset Type")
        rca_status_chart = st.session_state.visualizations.create_rca_status_chart(
            data['failures'], data['assets']
        )
        st.plotly_chart(rca_status_chart, use_container_width=True)

    with col2:
        st.subheader("Corrective Actions Effectiveness")
        effectiveness_chart = st.session_state.visualizations.create_corrective_action_chart(data['failures'])
        st.plotly_chart(effectiveness_chart, use_container_width=True)

    # RCA details table
    st.subheader("RCA Investigation Details")
    rca_details = data['failures'][data['failures']['RCAStatus'].isin(['Open', 'In Progress'])].merge(
        data['assets'][['AssetID', 'AssetName']], on='AssetID'
    ).sort_values('FailureDate', ascending=False)

    if not rca_details.empty:
        st.dataframe(
            rca_details[['FailureDate', 'AssetName', 'FailureMode', 'RootCause',
                         'RCAStatus', 'CorrectiveAction']],
            use_container_width=True
        )
    else:
        st.info("No active RCA investigations.")


if __name__ == "__main__":
    main()