# src/model/__init__.py

# Import all model classes
from .Schools import   Schools
from .Sessions import  Sessions
from .ClassData import ClassData
from .FeesData import  FeesData
from .StudentsDB import StudentsDB
from .StudentSessions import StudentSessions
from .StudentsMarks import StudentsMarks
from .TeachersLogin import TeachersLogin

# Optional: control what `from src.model import *` brings in
__all__ = [
    "Schools",
    "Sessions",
    "ClassData",
    "FeesData",
    "StudentsDB",
    "StudentSessions",
    "StudentsMarks",
    "TeachersLogin",
]
