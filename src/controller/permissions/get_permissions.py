from src.model.Permissions import Permissions
from src.model.RolePermissions import RolePermissions
from src import db
from src.model.StaffPermissions import StaffPermissions

def get_permissions(user_id, role_id):

    permissions_list = set()  #set for unique permissions

    role_permissions = (
            db.session.query(Permissions.permission_name)  #get all the permissions for the role
            .join(RolePermissions, RolePermissions.permission_id == Permissions.id)
            .filter(RolePermissions.role_id == role_id)
            .all()
        )
    
    staff_specific_permission = (
            db.session.query(StaffPermissions.is_granted, Permissions.permission_name)  # get the exceptional permissions for the staff, asigned or unassigned
            .join(StaffPermissions, StaffPermissions.permission_id == Permissions.id)
            .filter(StaffPermissions.staff_id == user_id)
            .all()
        )

    for role_permission in role_permissions:
        permissions_list.add(role_permission.permission_name)

    # Apply staff-specific changes
    for is_granted, permission_name in staff_specific_permission:
        if is_granted:
            permissions_list.add(permission_name)
        else:
            permissions_list.discard(permission_name)

    return list(permissions_list)