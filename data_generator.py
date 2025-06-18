"""
Mock data generator for RCM dashboard
Creates realistic test data based on Carl software data model
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import uuid
from data_models import Asset, WorkOrder, Failure, MaintenanceCost, AssetHierarchy, RCMDataModel


class DataGenerator:
    """Generates realistic mock data for RCM analytics"""

    def __init__(self, seed=42):
        random.seed(seed)
        np.random.seed(seed)

        # Configuration constants
        self.asset_types = ['Pump', 'Motor', 'Compressor', 'Valve', 'Heat Exchanger', 'Tank']
        self.locations = ['Plant A', 'Plant B', 'Plant C', 'Warehouse', 'Office Building']
        self.criticality_levels = ['Critical', 'High', 'Medium', 'Low']
        self.manufacturers = ['ABB', 'Siemens', 'Schneider', 'Emerson', 'Honeywell']
        self.failure_modes = [
            'Mechanical Wear', 'Electrical Failure', 'Corrosion', 'Vibration',
            'Overheating', 'Seal Failure', 'Bearing Failure', 'Control System Error'
        ]
        self.maintenance_types = ['Preventive', 'Corrective', 'Predictive', 'Emergency']
        self.root_causes = [
            'Inadequate Lubrication', 'Design Deficiency', 'Installation Error',
            'Operating Error', 'Maintenance Error', 'Environmental Factors',
            'Material Defect', 'Age/Wear'
        ]

    def generate_assets(self, count=100) -> pd.DataFrame:
        """Generate asset data"""
        assets = []

        for i in range(count):
            asset_type = random.choice(self.asset_types)
            location = random.choice(self.locations)
            criticality = np.random.choice(
                self.criticality_levels,
                p=[0.1, 0.3, 0.4, 0.2]  # Weight towards medium criticality
            )

            asset = Asset(
                AssetID=f"AST-{str(i + 1).zfill(4)}",
                AssetName=f"{asset_type}-{str(i + 1).zfill(3)}",
                AssetType=asset_type,
                AssetModel=f"Model-{random.randint(100, 999)}",
                Manufacturer=random.choice(self.manufacturers),
                SerialNumber=f"SN{random.randint(100000, 999999)}",
                InstallationDate=datetime.now() - timedelta(days=random.randint(30, 3650)),
                Location=location,
                CriticalityLevel=criticality,
                OperationalStatus=np.random.choice(['Active', 'Inactive', 'Maintenance'], p=[0.85, 0.10, 0.05]),
                ReplacementCost=random.uniform(5000, 500000),
                MaintenanceGroup=f"MG-{random.randint(1, 10)}"
            )
            assets.append(asset.__dict__)

        return pd.DataFrame(assets)

    def generate_work_orders(self, assets_df, count=500) -> pd.DataFrame:
        """Generate work order data"""
        work_orders = []

        for i in range(count):
            asset_id = random.choice(assets_df['AssetID'].values)
            maintenance_type = random.choice(self.maintenance_types)

            # Schedule date between 1 year ago and 3 months in future
            scheduled_date = datetime.now() - timedelta(days=random.randint(-90, 365))

            # Determine if work order is completed
            is_completed = scheduled_date < datetime.now() - timedelta(days=random.randint(0, 30))

            if is_completed:
                start_date = scheduled_date + timedelta(hours=random.randint(0, 48))
                actual_duration = random.uniform(1, 24)
                completion_date = start_date + timedelta(hours=actual_duration)
                status = 'Completed'
            else:
                start_date = None
                actual_duration = None
                completion_date = None
                status = random.choice(['Scheduled', 'In Progress'])

            work_order = WorkOrder(
                WorkOrderID=f"WO-{str(i + 1).zfill(6)}",
                AssetID=asset_id,
                MaintenanceType=maintenance_type,
                Description=f"{maintenance_type} maintenance for {asset_id}",
                Status=status,
                Priority=random.choice(['Critical', 'High', 'Medium', 'Low']),
                ScheduledDate=scheduled_date,
                StartDate=start_date,
                CompletionDate=completion_date,
                EstimatedDuration=random.uniform(2, 16),
                ActualDuration=actual_duration,
                TotalCost=random.uniform(500, 15000),
                AssignedTechnician=f"Tech-{random.randint(1, 20)}"
            )
            work_orders.append(work_order.__dict__)

        return pd.DataFrame(work_orders)

    def generate_failures(self, assets_df, count=300) -> pd.DataFrame:
        """Generate failure data"""
        failures = []

        for i in range(count):
            asset_id = random.choice(assets_df['AssetID'].values)
            failure_date = datetime.now() - timedelta(days=random.randint(1, 730))

            # Get asset criticality to influence failure severity
            asset_criticality = assets_df[assets_df['AssetID'] == asset_id]['CriticalityLevel'].iloc[0]

            if asset_criticality == 'Critical':
                severity_weights = [0.4, 0.3, 0.2, 0.1]
            elif asset_criticality == 'High':
                severity_weights = [0.2, 0.4, 0.3, 0.1]
            else:
                severity_weights = [0.1, 0.2, 0.4, 0.3]

            severity = np.random.choice(['Critical', 'High', 'Medium', 'Low'], p=severity_weights)

            # Downtime based on severity
            if severity == 'Critical':
                downtime = random.uniform(24, 168)  # 1-7 days
            elif severity == 'High':
                downtime = random.uniform(8, 48)  # 8-48 hours
            elif severity == 'Medium':
                downtime = random.uniform(2, 16)  # 2-16 hours
            else:
                downtime = random.uniform(0.5, 8)  # 0.5-8 hours

            rca_status = random.choice(['Open', 'In Progress', 'Completed'])
            rca_resolution_days = random.uniform(5, 60) if rca_status == 'Completed' else None

            failure = Failure(
                FailureID=f"FAIL-{str(i + 1).zfill(6)}",
                AssetID=asset_id,
                FailureDate=failure_date,
                FailureMode=random.choice(self.failure_modes),
                FailureDescription=f"Equipment failure - {random.choice(self.failure_modes)}",
                Severity=severity,
                DowntimeHours=downtime,
                RepairCost=random.uniform(1000, 50000),
                RootCause=random.choice(self.root_causes),
                CorrectiveAction=f"Corrective action for {random.choice(self.root_causes)}",
                RCAStatus=rca_status,
                RCAResolutionDays=rca_resolution_days
            )
            failures.append(failure.__dict__)

        return pd.DataFrame(failures)

    def generate_maintenance_costs(self, assets_df, work_orders_df, count=800) -> pd.DataFrame:
        """Generate maintenance cost data"""
        costs = []
        cost_types = ['Labor', 'Parts', 'External', 'Equipment']

        for i in range(count):
            asset_id = random.choice(assets_df['AssetID'].values)
            cost_date = datetime.now() - timedelta(days=random.randint(1, 730))
            cost_type = random.choice(cost_types)

            # Link some costs to work orders
            work_order_id = None
            if random.random() < 0.7:  # 70% chance of being linked to a work order
                asset_work_orders = work_orders_df[work_orders_df['AssetID'] == asset_id]
                if not asset_work_orders.empty:
                    work_order_id = random.choice(asset_work_orders['WorkOrderID'].values)

            # Cost varies by type
            if cost_type == 'Labor':
                amount = random.uniform(200, 2000)
            elif cost_type == 'Parts':
                amount = random.uniform(100, 10000)
            elif cost_type == 'External':
                amount = random.uniform(500, 20000)
            else:  # Equipment
                amount = random.uniform(1000, 50000)

            cost = MaintenanceCost(
                CostID=f"COST-{str(i + 1).zfill(6)}",
                AssetID=asset_id,
                Date=cost_date,
                CostType=cost_type,
                Amount=amount,
                Description=f"{cost_type} cost for {asset_id}",
                WorkOrderID=work_order_id
            )
            costs.append(cost.__dict__)

        return pd.DataFrame(costs)

    def generate_all_data(self) -> dict:
        """Generate complete dataset for RCM dashboard"""
        # Generate base data
        assets_df = self.generate_assets(100)
        work_orders_df = self.generate_work_orders(assets_df, 500)
        failures_df = self.generate_failures(assets_df, 300)
        maintenance_costs_df = self.generate_maintenance_costs(assets_df, work_orders_df, 800)

        return {
            'assets': assets_df,
            'work_orders': work_orders_df,
            'failures': failures_df,
            'maintenance_costs': maintenance_costs_df
        }
