"""
KPI calculation engine for RCM analytics
Calculates key performance indicators like MTBF, MTTR, OEE, etc.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class KPICalculator:
    """Calculates key performance indicators for RCM analytics"""

    def __init__(self):
        self.calculation_period_days = 90  # Default period for trend calculations

    def calculate_mtbf(self, failures_df: pd.DataFrame, assets_df: pd.DataFrame) -> dict:
        """Calculate Mean Time Between Failures"""
        if failures_df.empty:
            return {'mtbf': 0, 'mtbf_change': 0}

        # Group failures by asset and calculate time between failures
        mtbf_by_asset = []

        for asset_id in failures_df['AssetID'].unique():
            asset_failures = failures_df[failures_df['AssetID'] == asset_id].sort_values('FailureDate')

            if len(asset_failures) > 1:
                time_diffs = asset_failures['FailureDate'].diff().dt.total_seconds() / (24 * 3600)  # days
                mtbf_by_asset.extend(time_diffs.dropna().tolist())

        if not mtbf_by_asset:
            return {'mtbf': 0, 'mtbf_change': 0}

        current_mtbf = np.mean(mtbf_by_asset)

        # Calculate trend (last 30 days vs previous 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_failures = failures_df[failures_df['FailureDate'] >= cutoff_date]
        previous_failures = failures_df[
            (failures_df['FailureDate'] >= cutoff_date - timedelta(days=30)) &
            (failures_df['FailureDate'] < cutoff_date)
            ]

        if len(recent_failures) > 0 and len(previous_failures) > 0:
            mtbf_change = ((len(previous_failures) - len(recent_failures)) / len(previous_failures)) * 100
        else:
            mtbf_change = 0

        return {'mtbf': current_mtbf, 'mtbf_change': mtbf_change}

    def calculate_mttr(self, failures_df: pd.DataFrame) -> dict:
        """Calculate Mean Time to Repair"""
        if failures_df.empty or 'DowntimeHours' not in failures_df.columns:
            return {'mttr': 0, 'mttr_change': 0}

        current_mttr = failures_df['DowntimeHours'].mean()

        # Calculate trend
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_failures = failures_df[failures_df['FailureDate'] >= cutoff_date]
        previous_failures = failures_df[
            (failures_df['FailureDate'] >= cutoff_date - timedelta(days=30)) &
            (failures_df['FailureDate'] < cutoff_date)
            ]

        if not recent_failures.empty and not previous_failures.empty:
            recent_mttr = recent_failures['DowntimeHours'].mean()
            previous_mttr = previous_failures['DowntimeHours'].mean()
            mttr_change = ((previous_mttr - recent_mttr) / previous_mttr) * 100
        else:
            mttr_change = 0

        return {'mttr': current_mttr, 'mttr_change': mttr_change}

    def calculate_oee(self, assets_df: pd.DataFrame, failures_df: pd.DataFrame) -> dict:
        """Calculate Overall Equipment Effectiveness"""
        if assets_df.empty:
            return {'oee': 0, 'oee_change': 0}

        # Simplified OEE calculation based on availability
        total_assets = len(assets_df[assets_df['OperationalStatus'] == 'Active'])

        if total_assets == 0:
            return {'oee': 0, 'oee_change': 0}

        # Calculate availability based on recent failures
        recent_failures = failures_df[
            failures_df['FailureDate'] >= datetime.now() - timedelta(days=30)
            ]

        total_downtime = recent_failures['DowntimeHours'].sum()
        total_possible_time = total_assets * 30 * 24  # 30 days * 24 hours

        availability = max(0, (total_possible_time - total_downtime) / total_possible_time)

        # Assume quality and performance rates (would need more data in real system)
        quality_rate = 0.95
        performance_rate = 0.90

        oee = availability * quality_rate * performance_rate * 100

        # Calculate trend (simplified)
        oee_change = np.random.uniform(-5, 5)  # Placeholder for trend calculation

        return {'oee': oee, 'oee_change': oee_change}

    def calculate_total_maintenance_cost(self, maintenance_costs_df: pd.DataFrame) -> dict:
        """Calculate total maintenance costs and trend"""
        if maintenance_costs_df.empty:
            return {'total_cost': 0, 'cost_change': 0}

        # Current month costs
        current_month_start = datetime.now().replace(day=1)
        current_costs = maintenance_costs_df[
            maintenance_costs_df['Date'] >= current_month_start
            ]['Amount'].sum()

        # Previous month costs
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        previous_costs = maintenance_costs_df[
            (maintenance_costs_df['Date'] >= previous_month_start) &
            (maintenance_costs_df['Date'] < current_month_start)
            ]['Amount'].sum()

        if previous_costs > 0:
            cost_change = ((current_costs - previous_costs) / previous_costs) * 100
        else:
            cost_change = 0

        total_cost = maintenance_costs_df['Amount'].sum()

        return {'total_cost': total_cost, 'cost_change': cost_change}

    def calculate_asset_utilization(self, assets_df: pd.DataFrame) -> dict:
        """Calculate asset utilization metrics"""
        if assets_df.empty:
            return {'utilization': 0, 'active_assets': 0, 'total_assets': 0}

        total_assets = len(assets_df)
        active_assets = len(assets_df[assets_df['OperationalStatus'] == 'Active'])
        utilization = (active_assets / total_assets) * 100 if total_assets > 0 else 0

        return {
            'utilization': utilization,
            'active_assets': active_assets,
            'total_assets': total_assets
        }

    def calculate_failure_rate(self, failures_df: pd.DataFrame, period_days: int = 30) -> dict:
        """Calculate failure rate per period"""
        if failures_df.empty:
            return {'failure_rate': 0, 'total_failures': 0}

        cutoff_date = datetime.now() - timedelta(days=period_days)
        recent_failures = failures_df[failures_df['FailureDate'] >= cutoff_date]

        failure_rate = len(recent_failures) / period_days  # failures per day

        return {
            'failure_rate': failure_rate,
            'total_failures': len(recent_failures)
        }

    def calculate_criticality_distribution(self, assets_df: pd.DataFrame) -> dict:
        """Calculate distribution of assets by criticality level"""
        if assets_df.empty:
            return {}

        criticality_counts = assets_df['CriticalityLevel'].value_counts().to_dict()
        total_assets = len(assets_df)

        criticality_percentages = {
            level: (count / total_assets) * 100
            for level, count in criticality_counts.items()
        }

        return criticality_percentages

    def calculate_all_kpis(self, data: dict) -> dict:
        """Calculate all key performance indicators"""
        assets_df = data['assets']
        failures_df = data['failures']
        maintenance_costs_df = data['maintenance_costs']

        mtbf_data = self.calculate_mtbf(failures_df, assets_df)
        mttr_data = self.calculate_mttr(failures_df)
        oee_data = self.calculate_oee(assets_df, failures_df)
        cost_data = self.calculate_total_maintenance_cost(maintenance_costs_df)
        utilization_data = self.calculate_asset_utilization(assets_df)
        failure_rate_data = self.calculate_failure_rate(failures_df)
        criticality_data = self.calculate_criticality_distribution(assets_df)

        return {
            'mtbf': mtbf_data['mtbf'],
            'mtbf_change': mtbf_data['mtbf_change'],
            'mttr': mttr_data['mttr'],
            'mttr_change': mttr_data['mttr_change'],
            'oee': oee_data['oee'],
            'oee_change': oee_data['oee_change'],
            'total_cost': cost_data['total_cost'],
            'cost_change': cost_data['cost_change'],
            'utilization': utilization_data['utilization'],
            'active_assets': utilization_data['active_assets'],
            'total_assets': utilization_data['total_assets'],
            'failure_rate': failure_rate_data['failure_rate'],
            'total_failures': failure_rate_data['total_failures'],
            'criticality_distribution': criticality_data
        }
