""" base.py
    This file will contain all base classes here.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey  # noqa: F401
from sqlalchemy.orm import relationship, backref  # noqa: F401
from sqlalchemy.sql import func

from sqlalchemy.ext.declarative import declarative_base

from .utils import flatten

###############################################################################
# base class for all models
BaseModel = declarative_base()


class ModelMixin():
    creator_id = Column('N_CREATOR_ID', Integer(), nullable=False)
    owner_id = Column('N_OWNER_ID', Integer(), nullable=False)
    in_use = Column('N_INUSE', Integer(), nullable=False, default=1)
    create_on = Column('D_CREATE', DateTime(),
                       nullable=False, default=func.now())
    update_on = Column('D_UPDATE', DateTime(), nullable=False)


class FormMixin(object):
    """ base class for all forms. As a mixin, it will inject functions into these subclasses
    """

    def skip_csrf_validation(self):
        if hasattr(self, '_fields') and 'csrf_token' in self._fields:
            del self._fields['csrf_token']

    def extract_errors(self, sep='; '):
        return sep.join(flatten(self.errors.values())) if self.errors and len(self.errors) > 0 else ''
