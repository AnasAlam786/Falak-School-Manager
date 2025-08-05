from src.model.Permissions import Permissions
from src.model.RolePermissions import RolePermissions
from src import db

def get_permissions(user_id):
    perms = (
            db.session.query(Permissions.permission_name)
            .join(RolePermissions, RolePermissions.permission_id == Permissions.id)
            .filter(RolePermissions.role_id == user_id)
            .all()
        )
    return [p.permission_name for p in perms]