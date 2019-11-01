from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey  # noqa: F401
from sqlalchemy.orm import relationship, backref  # noqa: F401
# from sqlalchemy.sql import func

from .base import BaseModel, ModelMixin
###############################################################################


class Project(BaseModel, ModelMixin):
    __tablename__ = 'KA_PROJECTS'

    id = Column('N_PROJ_ID', Integer(), primary_key=True, autoincrement=True)
    name = Column('C_NAME', String(80), unique=True, nullable=False)
    description = Column('C_DESC', String(255))


# class DBVarsModel(BaseModel):
#     __tablename__ = 'DB_VARS'
#     # - id
#     # - table_id
#     # - name
#     # - display name
#     # - external name
#     # - source table
#     # - source column
#     # - biz_category
#     # - data_type
#     # - logic_type
#     # - description
#     # - url_detail


# class DBTableModel(BaseModel):
#     __tablename__ = 'DB_TABLES'
#     # - id


# class DBProjectModel(BaseModel):
#     __tablename__ = 'DB_PROJECTS'
#     # - id

###############################################################################
