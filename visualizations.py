"""
Visualization components for RCM dashboard
Creates all charts and graphs using Plotly
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class RCMVisualizations:
    """Creates visualizations for RCM dashboard"""

    def __init__(self):
        self.color_palette = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'warning': '#ff9800',
            'danger': '#d62728',
            'info': '#17a2b8'
        }

        self.criticality_colors = {
            'Critical': '#d62728',
            'High': '#ff7f0e',
            'Medium': '#2ca02c',
            'Low': '#1f77b4'
        }

    def create_criticality_pie_chart(self, assets_df: pd.DataFrame) -> go.Figure:
        """Create asset criticality distribution pie chart"""
        if assets_df.empty:
            return go.Figure().add_annotation(text="No data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        criticality_counts = assets_df['CriticalityLevel'].value_counts()

        fig = go.Figure(data=[go.Pie(
            labels=criticality_counts.index,
            values=criticality_counts.values,
            hole=0.4,
            marker_colors=[self.criticality_colors.get(level, '#1f77b4')
                           for level in criticality_counts.index]
        )])

        fig.update_layout(
            title="Asset Criticality Distribution",
            showlegend=True,
            height=400
        )

        return fig

    def create_cost_trend_chart(self, maintenance_costs_df: pd.DataFrame) -> go.Figure:
        """Create monthly maintenance costs trend chart"""
        if maintenance_costs_df.empty:
            return go.Figure().add_annotation(text="No cost data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Group by month and cost type
        costs_df = maintenance_costs_df.copy()
        costs_df['YearMonth'] = costs_df['Date'].dt.to_period('M')

        monthly_costs = costs_df.groupby(['YearMonth', 'CostType'])['Amount'].sum().unstack(fill_value=0)
        monthly_costs.index = monthly_costs.index.to_timestamp()

        fig = go.Figure()

        for cost_type in monthly_costs.columns:
            fig.add_trace(go.Scatter(
                x=monthly_costs.index,
                y=monthly_costs[cost_type],
                mode='lines+markers',
                name=cost_type,
                stackgroup='one'
            ))

        fig.update_layout(
            title="Monthly Maintenance Costs by Type",
            xaxis_title="Month",
            yaxis_title="Cost ($)",
            hovermode='x unified',
            height=400
        )

        return fig

    def create_asset_heatmap(self, assets_df: pd.DataFrame, failures_df: pd.DataFrame) -> go.Figure:
        """Create asset status heatmap"""
        if assets_df.empty:
            return go.Figure().add_annotation(text="No asset data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Create failure count by asset
        failure_counts = failures_df.groupby('AssetID').size().reset_index(name='FailureCount')

        # Merge with assets
        heatmap_data = assets_df.merge(failure_counts, on='AssetID', how='left')
        heatmap_data['FailureCount'] = heatmap_data['FailureCount'].fillna(0)

        # Create pivot table for heatmap
        pivot_data = heatmap_data.pivot_table(
            values='FailureCount',
            index='Location',
            columns='AssetType',
            aggfunc='mean',
            fill_value=0
        )

        fig = go.Figure(data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale='Reds',
            text=pivot_data.values,
            texttemplate="%{text:.1f}",
            textfont={"size": 10}
        ))

        fig.update_layout(
            title="Average Failure Count by Location and Asset Type",
            xaxis_title="Asset Type",
            yaxis_title="Location",
            height=400
        )

        return fig

    def create_failure_pareto_chart(self, failures_df: pd.DataFrame) -> go.Figure:
        """Create Pareto chart for failure modes"""
        if failures_df.empty:
            return go.Figure().add_annotation(text="No failure data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Count failures by mode
        failure_counts = failures_df['FailureMode'].value_counts()
        cumulative_pct = (failure_counts.cumsum() / failure_counts.sum()) * 100

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Bar chart
        fig.add_trace(
            go.Bar(x=failure_counts.index, y=failure_counts.values,
                   name="Failure Count", marker_color=self.color_palette['primary']),
            secondary_y=False,
        )

        # Line chart for cumulative percentage
        fig.add_trace(
            go.Scatter(x=failure_counts.index, y=cumulative_pct.values,
                       mode='lines+markers', name="Cumulative %",
                       line=dict(color=self.color_palette['danger'], width=3)),
            secondary_y=True,
        )

        fig.update_xaxes(title_text="Failure Mode")
        fig.update_yaxes(title_text="Number of Failures", secondary_y=False)
        fig.update_yaxes(title_text="Cumulative Percentage", secondary_y=True)

        fig.update_layout(
            title="Failure Mode Pareto Analysis",
            height=500
        )

        return fig

    def create_failure_by_asset_chart(self, failures_df: pd.DataFrame, assets_df: pd.DataFrame) -> go.Figure:
        """Create failure distribution by asset type"""
        if failures_df.empty or assets_df.empty:
            return go.Figure().add_annotation(text="No data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Merge failures with assets
        merged_df = failures_df.merge(assets_df[['AssetID', 'AssetType']], on='AssetID')
        failure_by_type = merged_df['AssetType'].value_counts()

        fig = go.Figure(data=[go.Bar(
            x=failure_by_type.index,
            y=failure_by_type.values,
            marker_color=self.color_palette['secondary']
        )])

        fig.update_layout(
            title="Failures by Asset Type",
            xaxis_title="Asset Type",
            yaxis_title="Number of Failures",
            height=400
        )

        return fig

    def create_failure_severity_chart(self, failures_df: pd.DataFrame) -> go.Figure:
        """Create failure severity distribution chart"""
        if failures_df.empty:
            return go.Figure().add_annotation(text="No failure data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        severity_counts = failures_df['Severity'].value_counts()

        fig = go.Figure(data=[go.Bar(
            x=severity_counts.index,
            y=severity_counts.values,
            marker_color=[self.criticality_colors.get(severity, '#1f77b4')
                          for severity in severity_counts.index]
        )])

        fig.update_layout(
            title="Failure Severity Distribution",
            xaxis_title="Severity Level",
            yaxis_title="Number of Failures",
            height=400
        )

        return fig

    def create_location_failure_heatmap(self, failures_df: pd.DataFrame, assets_df: pd.DataFrame) -> go.Figure:
        """Create failure frequency heatmap by location"""
        if failures_df.empty or assets_df.empty:
            return go.Figure().add_annotation(text="No data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Merge failures with assets for location info
        merged_df = failures_df.merge(assets_df[['AssetID', 'Location']], on='AssetID')

        # Group by location and month
        merged_df['YearMonth'] = merged_df['FailureDate'].dt.to_period('M')
        location_month_failures = merged_df.groupby(['Location', 'YearMonth']).size().unstack(fill_value=0)

        if location_month_failures.empty:
            return go.Figure().add_annotation(text="No data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        fig = go.Figure(data=go.Heatmap(
            z=location_month_failures.values,
            x=[str(col) for col in location_month_failures.columns],
            y=location_month_failures.index,
            colorscale='Blues'
        ))

        fig.update_layout(
            title="Failure Frequency by Location and Month",
            xaxis_title="Month",
            yaxis_title="Location",
            height=400
        )

        return fig

    def create_failure_trend_chart(self, failures_df: pd.DataFrame) -> go.Figure:
        """Create failure rate trend chart"""
        if failures_df.empty:
            return go.Figure().add_annotation(text="No failure data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Group failures by month
        failures_df['YearMonth'] = failures_df['FailureDate'].dt.to_period('M')
        monthly_failures = failures_df.groupby('YearMonth').size()
        monthly_failures.index = monthly_failures.index.to_timestamp()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=monthly_failures.index,
            y=monthly_failures.values,
            mode='lines+markers',
            name='Monthly Failures',
            line=dict(color=self.color_palette['danger'], width=3)
        ))

        # Add trend line
        x_numeric = np.arange(len(monthly_failures))
        z = np.polyfit(x_numeric, monthly_failures.values, 1)
        p = np.poly1d(z)

        fig.add_trace(go.Scatter(
            x=monthly_failures.index,
            y=p(x_numeric),
            mode='lines',
            name='Trend',
            line=dict(color=self.color_palette['warning'], dash='dash')
        ))

        fig.update_layout(
            title="Failure Rate Trend Analysis",
            xaxis_title="Month",
            yaxis_title="Number of Failures",
            height=400
        )

        return fig

    def create_mtbf_trend_chart(self, failures_df: pd.DataFrame, assets_df: pd.DataFrame) -> go.Figure:
        """Create MTBF trend chart by asset type"""
        if failures_df.empty or assets_df.empty:
            return go.Figure().add_annotation(text="No data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Merge with assets for asset type
        merged_df = failures_df.merge(assets_df[['AssetID', 'AssetType']], on='AssetID')

        # Calculate MTBF by asset type and month
        merged_df['YearMonth'] = merged_df['FailureDate'].dt.to_period('M')

        fig = go.Figure()

        for asset_type in merged_df['AssetType'].unique()[:5]:  # Top 5 asset types
            type_data = merged_df[merged_df['AssetType'] == asset_type]
            monthly_counts = type_data.groupby('YearMonth').size()

            if len(monthly_counts) > 1:
                # Calculate MTBF (simplified as days between failures)
                mtbf_values = []
                for i in range(1, len(monthly_counts)):
                    days_in_month = 30
                    failures_in_month = monthly_counts.iloc[i]
                    mtbf = days_in_month / failures_in_month if failures_in_month > 0 else days_in_month
                    mtbf_values.append(mtbf)

                if mtbf_values:
                    fig.add_trace(go.Scatter(
                        x=monthly_counts.index[1:].to_timestamp(),
                        y=mtbf_values,
                        mode='lines+markers',
                        name=f'{asset_type} MTBF'
                    ))

        fig.update_layout(
            title="MTBF Trend by Asset Type",
            xaxis_title="Month",
            yaxis_title="MTBF (Days)",
            height=400
        )

        return fig

    def create_mttr_trend_chart(self, failures_df: pd.DataFrame) -> go.Figure:
        """Create MTTR trend chart"""
        if failures_df.empty or 'DowntimeHours' not in failures_df.columns:
            return go.Figure().add_annotation(text="No downtime data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Group by month and calculate average downtime
        failures_df['YearMonth'] = failures_df['FailureDate'].dt.to_period('M')
        monthly_mttr = failures_df.groupby('YearMonth')['DowntimeHours'].mean()
        monthly_mttr.index = monthly_mttr.index.to_timestamp()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=monthly_mttr.index,
            y=monthly_mttr.values,
            mode='lines+markers',
            name='Monthly MTTR',
            line=dict(color=self.color_palette['info'], width=3)
        ))

        fig.update_layout(
            title="MTTR Trend Analysis",
            xaxis_title="Month",
            yaxis_title="MTTR (Hours)",
            height=400
        )

        return fig

    def create_cost_category_trend(self, maintenance_costs_df: pd.DataFrame) -> go.Figure:
        """Create maintenance cost trends by category"""
        if maintenance_costs_df.empty:
            return go.Figure().add_annotation(text="No cost data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Group by month and cost type
        costs_df = maintenance_costs_df.copy()
        costs_df['YearMonth'] = costs_df['Date'].dt.to_period('M')

        monthly_costs = costs_df.groupby(['YearMonth', 'CostType'])['Amount'].sum().unstack(fill_value=0)
        monthly_costs.index = monthly_costs.index.to_timestamp()

        fig = go.Figure()

        colors = [self.color_palette['primary'], self.color_palette['secondary'],
                  self.color_palette['success'], self.color_palette['warning']]

        for i, cost_type in enumerate(monthly_costs.columns):
            fig.add_trace(go.Scatter(
                x=monthly_costs.index,
                y=monthly_costs[cost_type],
                mode='lines+markers',
                name=cost_type,
                line=dict(color=colors[i % len(colors)], width=2)
            ))

        fig.update_layout(
            title="Maintenance Cost Trends by Category",
            xaxis_title="Month",
            yaxis_title="Cost ($)",
            height=500
        )

        return fig

    def create_maintenance_gantt(self, work_orders_df: pd.DataFrame) -> go.Figure:
        """Create Gantt chart for maintenance activities"""
        if work_orders_df.empty:
            return go.Figure().add_annotation(text="No work order data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Filter recent work orders
        recent_orders = work_orders_df[
            work_orders_df['ScheduledDate'] >= datetime.now() - timedelta(days=30)
            ].head(20)  # Limit to 20 for readability

        if recent_orders.empty:
            return go.Figure().add_annotation(text="No recent work orders",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        fig = go.Figure()

        for i, row in recent_orders.iterrows():
            start_date = row['StartDate'] if pd.notna(row['StartDate']) else row['ScheduledDate']
            end_date = row['CompletionDate'] if pd.notna(row['CompletionDate']) else start_date + timedelta(
                hours=row['EstimatedDuration'])

            color = self.criticality_colors.get(row['Priority'], self.color_palette['primary'])

            fig.add_trace(go.Scatter(
                x=[start_date, end_date],
                y=[row['WorkOrderID'], row['WorkOrderID']],
                mode='lines',
                line=dict(color=color, width=10),
                name=row['Priority'],
                showlegend=False,
                hovertemplate=f"<b>{row['WorkOrderID']}</b><br>Type: {row['MaintenanceType']}<br>Priority: {row['Priority']}<extra></extra>"
            ))

        fig.update_layout(
            title="Maintenance Schedule Timeline",
            xaxis_title="Date",
            yaxis_title="Work Order ID",
            height=600,
            yaxis=dict(type='category')
        )

        return fig

    def create_schedule_compliance_chart(self, work_orders_df: pd.DataFrame) -> go.Figure:
        """Create schedule compliance chart"""
        if work_orders_df.empty:
            return go.Figure().add_annotation(text="No work order data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        completed_orders = work_orders_df[work_orders_df['Status'] == 'Completed'].copy()

        if completed_orders.empty:
            return go.Figure().add_annotation(text="No completed work orders",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Calculate compliance (on-time completion)
        completed_orders['OnTime'] = completed_orders['CompletionDate'] <= completed_orders['ScheduledDate']
        compliance_rate = completed_orders['OnTime'].mean() * 100

        fig = go.Figure(data=[go.Pie(
            labels=['On Time', 'Late'],
            values=[compliance_rate, 100 - compliance_rate],
            hole=0.4,
            marker_colors=[self.color_palette['success'], self.color_palette['danger']]
        )])

        fig.update_layout(
            title=f"Schedule Compliance ({compliance_rate:.1f}% On Time)",
            height=400
        )

        return fig

    def create_maintenance_type_chart(self, work_orders_df: pd.DataFrame) -> go.Figure:
        """Create maintenance type distribution chart"""
        if work_orders_df.empty:
            return go.Figure().add_annotation(text="No work order data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        type_counts = work_orders_df['MaintenanceType'].value_counts()

        fig = go.Figure(data=[go.Bar(
            x=type_counts.index,
            y=type_counts.values,
            marker_color=self.color_palette['info']
        )])

        fig.update_layout(
            title="Maintenance Type Distribution",
            xaxis_title="Maintenance Type",
            yaxis_title="Number of Work Orders",
            height=400
        )

        return fig

    def create_rca_categories_chart(self, failures_df: pd.DataFrame) -> go.Figure:
        """Create root cause categories chart"""
        if failures_df.empty:
            return go.Figure().add_annotation(text="No failure data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        root_cause_counts = failures_df['RootCause'].value_counts()

        fig = go.Figure(data=[go.Bar(
            x=root_cause_counts.values,
            y=root_cause_counts.index,
            orientation='h',
            marker_color=self.color_palette['warning']
        )])

        fig.update_layout(
            title="Root Cause Categories",
            xaxis_title="Number of Occurrences",
            yaxis_title="Root Cause",
            height=500
        )

        return fig

    def create_rca_status_chart(self, failures_df: pd.DataFrame, assets_df: pd.DataFrame) -> go.Figure:
        """Create RCA status by asset type chart"""
        if failures_df.empty or assets_df.empty:
            return go.Figure().add_annotation(text="No data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Merge with assets for asset type
        merged_df = failures_df.merge(assets_df[['AssetID', 'AssetType']], on='AssetID')

        # Group by asset type and RCA status
        rca_pivot = merged_df.groupby(['AssetType', 'RCAStatus']).size().unstack(fill_value=0)

        fig = go.Figure()

        status_colors = {
            'Open': self.color_palette['danger'],
            'In Progress': self.color_palette['warning'],
            'Completed': self.color_palette['success']
        }

        for status in rca_pivot.columns:
            fig.add_trace(go.Bar(
                name=status,
                x=rca_pivot.index,
                y=rca_pivot[status],
                marker_color=status_colors.get(status, self.color_palette['primary'])
            ))

        fig.update_layout(
            title="RCA Status by Asset Type",
            xaxis_title="Asset Type",
            yaxis_title="Number of RCAs",
            barmode='stack',
            height=400
        )

        return fig

    def create_corrective_action_chart(self, failures_df: pd.DataFrame) -> go.Figure:
        """Create corrective actions effectiveness chart"""
        if failures_df.empty:
            return go.Figure().add_annotation(text="No failure data available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Simulate effectiveness data (in real system, this would be calculated from repeat failures)
        completed_rcas = failures_df[failures_df['RCAStatus'] == 'Completed']

        if completed_rcas.empty:
            return go.Figure().add_annotation(text="No completed RCAs available",
                                              xref="paper", yref="paper",
                                              x=0.5, y=0.5, showarrow=False)

        # Group by corrective action type
        action_counts = completed_rcas['CorrectiveAction'].value_counts().head(10)

        # Simulate effectiveness percentages
        effectiveness = np.random.uniform(60, 95, len(action_counts))

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=action_counts.values,
            y=effectiveness,
            mode='markers',
            marker=dict(
                size=action_counts.values * 2,
                color=effectiveness,
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Effectiveness %")
            ),
            text=action_counts.index,
            hovertemplate="<b>%{text}</b><br>Count: %{x}<br>Effectiveness: %{y:.1f}%<extra></extra>"
        ))

        fig.update_layout(
            title="Corrective Actions Effectiveness",
            xaxis_title="Number of Actions Taken",
            yaxis_title="Effectiveness (%)",
            height=400
        )

        return fig
