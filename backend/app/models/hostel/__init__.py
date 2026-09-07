from app.models.hostel.hostel_building import HostelBuilding
from app.models.hostel.hostel_room import HostelRoom
from app.models.hostel.hostel_bed import HostelBed
from app.models.hostel.hostel_allocation import HostelAllocation
from app.models.hostel.hostel_attendance import HostelAttendance
from app.models.hostel.hostel_outpass import HostelOutpass
from app.models.hostel.hostel_fee import HostelFeeStructure, HostelFeeAllocation

__all__ = [
    "HostelBuilding",
    "HostelRoom",
    "HostelBed",
    "HostelAllocation",
    "HostelAttendance",
    "HostelOutpass",
    "HostelFeeStructure",
    "HostelFeeAllocation",
]
