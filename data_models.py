"""
Data models based on Carl software database schema
Simplified version focusing on RCM-relevant tables
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import pandas as pd


@dataclass
class Asset:
    """CSEQ_EQUIPMENT equivalent - Equipment/Asset information"""
    AssetID: str
    AssetName: str
    AssetType: str
    AssetModel: str
    Manufacturer: str
    SerialNumber: str
    InstallationDate: datetime
    Location: str
    CriticalityLevel: str  # Critical, High, Medium, Low
    OperationalStatus: str  # Active, Inactive, Maintenance
    ReplacementCost: float
    MaintenanceGroup: str


@dataclass
class WorkOrder:
    """CSMT_WORKORDER equivalent - Maintenance work orders"""
    WorkOrderID: str
    AssetID: str
    MaintenanceType: str  # Preventive, Corrective, Predictive
    Description: str
    Status: str  # Scheduled, In Progress, Completed, Cancelled
    Priority: str  # Critical, High, Medium, Low
    ScheduledDate: datetime
    StartDate: Optional[datetime]
    CompletionDate: Optional[datetime]
    EstimatedDuration: float  # hours
    ActualDuration: Optional[float]  # hours
    TotalCost: float
    AssignedTechnician: str


@dataclass
class Failure:
    """CSMT_FAILURE equivalent - Failure records"""
    FailureID: str
    AssetID: str
    FailureDate: datetime
    FailureMode: str
    FailureDescription: str
    Severity: str  # Critical, High, Medium, Low
    DowntimeHours: float
    RepairCost: float
    RootCause: str
    CorrectiveAction: str
    RCAStatus: str  # Open, In Progress, Completed
    RCAResolutionDays: Optional[float]


@dataclass
class MaintenanceCost:
    """CSFI_COSTCENTERMVT equivalent - Financial movements/costs"""
    CostID: str
    AssetID: str
    Date: datetime
    CostType: str  # Labor, Parts, External, Equipment
    Amount: float
    Description: str
    WorkOrderID: Optional[str]


@dataclass
class AssetHierarchy:
    """CSEQ_BOX equivalent - Asset structure hierarchy"""
    HierarchyID: str
    ParentAssetID: Optional[str]
    ChildAssetID: str
    HierarchyLevel: int
    HierarchyPath: str


class RCMDataModel:
    """Main data model class for RCM analytics"""

    def __init__(self):
        self.assets: List[Asset] = []
        self.work_orders: List[WorkOrder] = []
        self.failures: List[Failure] = []
        self.maintenance_costs: List[MaintenanceCost] = []
        self.asset_hierarchy: List[AssetHierarchy] = []

    def to_dataframes(self) -> dict:
        """Convert all data to pandas DataFrames for analysis"""
        return {
            'assets': pd.DataFrame([asset.__dict__ for asset in self.assets]),
            'work_orders': pd.DataFrame([wo.__dict__ for wo in self.work_orders]),
            'failures': pd.DataFrame([failure.__dict__ for failure in self.failures]),
            'maintenance_costs': pd.DataFrame([cost.__dict__ for cost in self.maintenance_costs]),
            'asset_hierarchy': pd.DataFrame([hier.__dict__ for hier in self.asset_hierarchy])
        }

    def get_asset_count(self) -> int:
        return len(self.assets)

    def get_active_assets(self) -> List[Asset]:
        return [asset for asset in self.assets if asset.OperationalStatus == 'Active']

    def get_critical_assets(self) -> List[Asset]:
        return [asset for asset in self.assets if asset.CriticalityLevel == 'Critical']

    def get_recent_failures(self, days: int = 30) -> List[Failure]:
        cutoff_date = datetime.now() - pd.Timedelta(days=days)
        return [failure for failure in self.failures if failure.FailureDate >= cutoff_date]

    def get_open_work_orders(self) -> List[WorkOrder]:
        return [wo for wo in self.work_orders if wo.Status in ['Scheduled', 'In Progress']]
