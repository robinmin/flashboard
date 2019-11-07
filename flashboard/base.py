""" base.py
    This file will contain all base classes here.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey  # noqa: F401
from sqlalchemy.orm import relationship, backref  # noqa: F401
from sqlalchemy.sql import func

from sqlalchemy.ext.declarative import declarative_base, declared_attr

from .utils import flatten

###############################################################################
# base class for all models
BaseModel = declarative_base()


class ModelMixin():
    @declared_attr
    def __table_args__(self):
        return {'quote': False, 'extend_existing': True}

    @declared_attr
    def in_use(self):
        return Column('n_inuse', Integer(), nullable=False, default=1, comment='Inuse flag')

    @declared_attr
    def creator_id(self):
        return Column('n_creator_id', Integer(), ForeignKey('sys_user.n_user_id'), nullable=False, comment='Creator ID')

    @declared_attr
    def updater_id(self):
        return Column('n_updater_id', Integer(), ForeignKey('sys_user.n_user_id'), nullable=True, comment='Updater ID')

    @declared_attr
    def create_on(self):
        return Column('d_create', DateTime(), nullable=False, default=func.now(), comment='Create date')

    @declared_attr
    def update_on(self):
        return Column('d_update', DateTime(), nullable=True, comment='Last update date')


class FormMixin(object):
    """ base class for all forms. As a mixin, it will inject functions into these subclasses
    """

    def skip_csrf_validation(self):
        if hasattr(self, '_fields') and 'csrf_token' in self._fields:
            del self._fields['csrf_token']

    def extract_errors(self, sep='; '):
        return sep.join(flatten(self.errors.values())) if self.errors and len(self.errors) > 0 else ''
