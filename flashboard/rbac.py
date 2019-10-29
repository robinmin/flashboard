import functools

from flask import abort, current_app
from flask_login import current_user

from config.rbac import RBAC_CONTROL, RBAC_ROLES
from .utils import flatten
from .services import UserService


def rbac_module(*module_names):
    """
    This decorator mark current view belong to which RBAC module
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            usvc = UserService()

            # get mapping
            mapped_roles = flatten([
                RBAC_CONTROL[module] if module in RBAC_CONTROL else None for module in module_names
            ])
            # de-duplicate
            mapped_roles = list(set(mapped_roles))

            # verify RBAC access control
            role_available = False
            for role in mapped_roles:
                if usvc.has_role(current_user, role):
                    role_available = True

            # access control
            try:
                if role_available:
                    return func(*args, **kwargs)
                else:
                    current_app.logger.warning('Invalid access!!')
                    abort(401)
            finally:
                pass
        return wrapper
    return decorator


def create_all_roles(drop_existing=False):
    """ create all pre-defined roles """

    from .database import db_trasaction
    from .models import RoleModel

    if drop_existing:
        RoleModel.query.delete()

    with db_trasaction() as txn:
        for role, desc in RBAC_ROLES.items():
            txn.save_item(RoleModel(role, desc))
