# src/model/__init__.py

# Import all model classes
from .Schools import Schools
from .Sessions import  Sessions
from .ClassData import ClassData
from .ClassAccess import ClassAccess

from .StudentsDB import StudentsDB
from .StudentSessions import StudentSessions
from .RTEInfo import RTEInfo
from .TeachersLogin import TeachersLogin

from .StudentsMarks_duplicate import StudentsMarks_duplicate
from .Subjects import Subjects
from .Exams import Exams

from .Roles import Roles
from .Permissions import Permissions
from .RolePermissions import RolePermissions

from .FeeData import  FeeData
from .FeeAmount import FeeAmount
from .FeeStructure import FeeStructure

# Optional: control what `from src.model import *` brings in
__all__ = [
    "Schools",
    "Sessions",
    "ClassData",
    "ClassAccess",
    
    "StudentsDB",
    "StudentSessions",
    "RTEInfo",
    "TeachersLogin",

    "StudentsMarks_duplicate",
    "Exams",
    "Subjects",

    
    "Roles",
    "Permissions",
    "RolePermissions",

    "FeeData",
    "FeeAmount",
    "FeeStructure",
]
