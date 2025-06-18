"""
Utility functions for RCM dashboard
"""

import pandas as pd
import streamlit as st
from datetime import datetime
import io
import base64


def format_currency(amount: float) -> str:
    """Format currency values"""
    if amount >= 1000000:
        return f"${amount / 1000000:.1f}M"
    elif amount >= 1000:
        return f"${amount / 1000:.1f}K"
    else:
        return f"${amount:.0f}"


def format_duration(hours: float) -> str:
    """Format duration in hours to human readable format"""
    if hours >= 24:
        days = hours / 24
        return f"{days:.1f} days"
    else:
        return f"{hours:.1f} hours"


def format_percentage(value: float) -> str:
    """Format percentage values"""
    return f"{value:.1f}%"


def export_data(data: dict, report_type: str = "general") -> None:
    """Export data to various formats"""
    try:
        # Create export DataFrame based on report type
        if report_type == "overview_report":
            export_df = create_overview_export(data)
        elif report_type == "failure_analysis":
            export_df = create_failure_analysis_export(data)
        else:
            export_df = create_general_export(data)

        # Convert to CSV
        csv_buffer = io.StringIO()
        export_df.to_csv(csv_buffer, index=False)
        csv_string = csv_buffer.getvalue()

        # Create download button
        b64 = base64.b64encode(csv_string.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{report_type}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv">Download CSV Report</a>'
        st.markdown(href, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")


def create_overview_export(data: dict) -> pd.DataFrame:
    """Create overview report export"""
    assets_df = data['assets']
    failures_df = data['failures']
    costs_df = data['maintenance_costs']

    # Merge data for comprehensive overview
    overview_data = assets_df.merge(
        failures_df.groupby('AssetID').agg({
            'FailureDate': 'count',
            'DowntimeHours': 'sum',
            'RepairCost': 'sum'
        }).rename(columns={
            'FailureDate': 'TotalFailures',
            'DowntimeHours': 'TotalDowntime',
            'RepairCost': 'TotalRepairCost'
        }).reset_index(),
        on='AssetID',
        how='left'
    )

    # Add maintenance costs
    maintenance_totals = costs_df.groupby('AssetID')['Amount'].sum().reset_index()
    maintenance_totals.columns = ['AssetID', 'TotalMaintenanceCost']

    overview_data = overview_data.merge(maintenance_totals, on='AssetID', how='left')

    # Fill NaN values
    overview_data = overview_data.fillna(0)

    return overview_data


def create_failure_analysis_export(data: dict) -> pd.DataFrame:
    """Create failure analysis export"""
    failures_df = data['failures']
    assets_df = data['assets']

    # Merge failures with asset information
    failure_analysis = failures_df.merge(
        assets_df[['AssetID', 'AssetName', 'AssetType', 'Location', 'CriticalityLevel']],
        on='AssetID',
        how='left'
    )

    return failure_analysis


def create_general_export(data: dict) -> pd.DataFrame:
    """Create general export with summary statistics"""
    summary_data = []

    # Asset summary
    assets_df = data['assets']
    asset_summary = {
        'Category': 'Assets',
        'Total_Count': len(assets_df),
        'Active_Count': len(assets_df[assets_df['OperationalStatus'] == 'Active']),
        'Critical_Count': len(assets_df[assets_df['CriticalityLevel'] == 'Critical']),
        'Total_Value': assets_df['ReplacementCost'].sum()
    }
    summary_data.append(asset_summary)

    # Failure summary
    failures_df = data['failures']
    failure_summary = {
        'Category': 'Failures',
        'Total_Count': len(failures_df),
        'Critical_Count': len(failures_df[failures_df['Severity'] == 'Critical']),
        'Total_Downtime': failures_df['DowntimeHours'].sum(),
        'Total_Cost': failures_df['RepairCost'].sum()
    }
    summary_data.append(failure_summary)

    # Work order summary
    work_orders_df = data['work_orders']
    wo_summary = {
        'Category': 'Work Orders',
        'Total_Count': len(work_orders_df),
        'Completed_Count': len(work_orders_df[work_orders_df['Status'] == 'Completed']),
        'Open_Count': len(work_orders_df[work_orders_df['Status'].isin(['Scheduled', 'In Progress'])]),
        'Total_Cost': work_orders_df['TotalCost'].sum()
    }
    summary_data.append(wo_summary)

    return pd.DataFrame(summary_data)


def calculate_availability(uptime_hours: float, total_hours: float) -> float:
    """Calculate equipment availability percentage"""
    if total_hours == 0:
        return 0
    return (uptime_hours / total_hours) * 100


def calculate_reliability(mtbf: float, target_mtbf: float) -> float:
    """Calculate reliability score based on MTBF"""
    if target_mtbf == 0:
        return 0
    return min(100, (mtbf / target_mtbf) * 100)


def get_criticality_color(criticality_level: str) -> str:
    """Get color code for criticality level"""
    colors = {
        'Critical': '#d62728',
        'High': '#ff7f0e',
        'Medium': '#2ca02c',
        'Low': '#1f77b4'
    }
    return colors.get(criticality_level, '#1f77b4')


def get_status_color(status: str) -> str:
    """Get color code for status"""
    colors = {
        'Active': '#2ca02c',
        'Inactive': '#d62728',
        'Maintenance': '#ff7f0e',
        'Completed': '#2ca02c',
        'In Progress': '#ff7f0e',
        'Scheduled': '#1f77b4',
        'Cancelled': '#d62728'
    }
    return colors.get(status, '#1f77b4')


def validate_data(data: dict) -> dict:
    """Validate and clean data"""
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    # Check for required columns
    required_columns = {
        'assets': ['AssetID', 'AssetName', 'AssetType', 'CriticalityLevel'],
        'failures': ['FailureID', 'AssetID', 'FailureDate', 'FailureMode'],
        'work_orders': ['WorkOrderID', 'AssetID', 'MaintenanceType', 'Status'],
        'maintenance_costs': ['CostID', 'AssetID', 'Date', 'Amount']
    }

    for table, columns in required_columns.items():
        if table in data:
            df = data[table]
            missing_columns = [col for col in columns if col not in df.columns]
            if missing_columns:
                validation_results['errors'].append(f"Missing columns in {table}: {missing_columns}")
                validation_results['valid'] = False

    # Check for data consistency
    if 'assets' in data and 'failures' in data:
        asset_ids = set(data['assets']['AssetID'])
        failure_asset_ids = set(data['failures']['AssetID'])
        orphaned_failures = failure_asset_ids - asset_ids

        if orphaned_failures:
            validation_results['warnings'].append(
                f"Failures reference non-existent assets: {len(orphaned_failures)} records")

    return validation_results


def create_data_summary(data: dict) -> dict:
    """Create data summary statistics"""
    summary = {}

    for table_name, df in data.items():
        if isinstance(df, pd.DataFrame):
            summary[table_name] = {
                'record_count': len(df),
                'columns': list(df.columns),
                'date_range': None
            }

            # Add date range if applicable
            date_columns = [col for col in df.columns if 'Date' in col or 'date' in col.lower()]
            if date_columns:
                date_col = date_columns[0]
                if pd.api.types.is_datetime64_any_dtype(df[date_col]):
                    summary[table_name]['date_range'] = {
                        'start': df[date_col].min(),
                        'end': df[date_col].max()
                    }

    return summary


@st.cache_data
def load_cached_data(data_generator_func):
    """Cache data loading for better performance"""
    return data_generator_func()


def display_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Display a metric card with styling"""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.metric(
            label=title,
            value=value,
            delta=delta,
            delta_color=delta_color
        )


def create_alert_message(alert_type: str, message: str):
    """Create styled alert messages"""
    if alert_type == "success":
        st.success(f"✅ {message}")
    elif alert_type == "warning":
        st.warning(f"⚠️ {message}")
    elif alert_type == "error":
        st.error(f"❌ {message}")
    elif alert_type == "info":
        st.info(f"ℹ️ {message}")
    else:
        st.write(message)
