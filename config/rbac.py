###############################################################################
#
# Define all roles
#
###############################################################################
RBAC_ROLES = {
    'anonymous': 'Anonymous User',
    'user':    'Normal User',
    'operator':  'Operator',
    'admin':     'Administrator',
}

# define default role for registered users
DEFAULT_ROLE = 'user'

###############################################################################
#
# This is the core of RBAC which defined the mapping between RBAC module and
# roles. The module of current view will be defined via decorator @rbac_module
#
###############################################################################
ALL_VALID_ROLES = RBAC_ROLES.keys()
ALL_ROLES = ['user', 'operator', 'admin']

RBAC_CONTROL = {
    'sys': ALL_VALID_ROLES,
    'home': ALL_ROLES,
}
