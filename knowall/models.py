import enum

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint  # noqa: F401
from sqlalchemy.types import Enum
from sqlalchemy.orm import relationship, backref  # noqa: F401
# from sqlalchemy.sql import func

from flashboard.base import BaseModel, ModelMixin
from flashboard.models import UserModel
###############################################################################


class ProjectModel(BaseModel, ModelMixin):
    __tablename__ = 'ka_projects'

    id = Column('n_proj_id', Integer(), primary_key=True,
                autoincrement=True, comment='ID')
    name = Column('c_name', String(80), unique=True,
                  nullable=False, comment='Name')
    description = Column('c_desc', String(255), comment='Description')

    owner_id = Column('n_owner_id', Integer(), ForeignKey(
        'sys_user.n_user_id'), comment='Owner ID')


class TableModel(BaseModel, ModelMixin):
    __tablename__ = 'ka_tables'
    __table_args__ = (
        UniqueConstraint('n_proj_id', 'c_name', name='uk_tables_name'),
    )

    id = Column('n_table_id', Integer(), primary_key=True,
                autoincrement=True, comment='ID')
    name = Column('c_name', String(80), nullable=False, comment='Name')
    description = Column('c_desc', String(
        255), comment='Description')

    proj_id = Column('n_proj_id', Integer(),
                     ForeignKey('ka_projects.n_proj_id'), comment='Project ID')
    owner_id = Column('n_owner_id', Integer(), ForeignKey(
        UserModel.id), comment='Owner ID')
    owner = relationship(UserModel, foreign_keys=owner_id)
    project = relationship(ProjectModel, foreign_keys=proj_id)


class EnumLogicType(enum.IntEnum):
    TEXT = 1
    NORMINAL = 2
    ORMINAL = 3
    BINARY = 4
    INTERNAL = 5
    RATIO = 6
    DATETIME = 7
    ID = 8

    def __str__(self):
        return self.name.capitalize()


class ColumnModel(BaseModel, ModelMixin):
    __tablename__ = 'ka_columns'
    __table_args__ = (
        UniqueConstraint('n_table_id', 'c_name', name='uk_columns_name'),
    )

    id = Column('n_col_id', Integer(), primary_key=True,
                autoincrement=True, comment='ID')
    name = Column('c_name', String(80), nullable=False, comment='Name')
    label = Column('c_label', String(80), nullable=False, comment='Label')
    external_name = Column('c_extrn_name', String(80), comment='External name')
    internal_name = Column('c_intrn_name', String(80), comment='Internal name')
    src_table = Column('c_src_tab', String(
        80), nullable=False, comment='Source table')
    src_col = Column('c_src_col', String(
        80), nullable=False, comment='Source column')
    src_type = Column('c_src_type', String(
        80), nullable=False, comment='Source type')
    biz_category = Column('c_biz_category', String(80),
                          comment='Business category')
    logic_type = Column('c_logic_type', Enum(
        EnumLogicType),  comment='Logic type')
    description = Column('c_desc', String(
        255), comment='Description')
    comments = Column('c_comments', String(
        255), comment='Comments')

    table_id = Column('n_table_id', Integer(),
                      ForeignKey('ka_tables.n_table_id'), comment='Table ID')
    table = relationship(TableModel, foreign_keys=table_id)
