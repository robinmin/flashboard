""" base.py
    This file will contain all base classes here.
"""

from sqlalchemy.ext.declarative import declarative_base

from .utils import flatten

###############################################################################
# base class for all models
BaseModel = declarative_base()


class FormMixin(object):
    """ base class for all forms. As a mixin, it will inject functions into these subclasses
    """

    def skip_csrf_validation(self):
        if hasattr(self, '_fields') and 'csrf_token' in self._fields:
            del self._fields['csrf_token']

    def extract_errors(self, sep='; '):
        return sep.join(flatten(self.errors.values())) if self.errors and len(self.errors) > 0 else ''
