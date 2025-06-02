# src/model/__init__.py

# Import all model classes
from .Schools import   Schools
from .Sessions import  Sessions
from .ClassData import ClassData
from .ClassAccess import ClassAccess

from .StudentsDB import StudentsDB
from .StudentSessions import StudentSessions
from .StudentsMarks import StudentsMarks
from .TeachersLogin import TeachersLogin

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
    "StudentsMarks",
    "TeachersLogin",
    
    "Roles",
    "Permissions",
    "RolePermissions",

    "FeeData",
    "FeeAmount",
    "FeeStructure",
]
