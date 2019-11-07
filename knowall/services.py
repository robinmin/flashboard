from sqlalchemy import and_

from flashboard.services import BaseService

from .models import ProjectModel, TableModel, ColumnModel
###############################################################################


class ProjectService(BaseService):
    def __init__(self):
        self.klass = ProjectModel

    def get_list(self, owner_id):
        """ get available project list """

        return self.klass.query.filter(self.klass.owner_id == owner_id)

    def get_detail(self, owner_id, proj_id):
        """ get available project list """

        return self.klass.query.filter(and_(
            self.klass.id == proj_id,
            self.klass.owner_id == owner_id,
        )).first()

    def create(self, name, description, owner_id):
        """ add new project """

        obj = self.klass()
        obj.name = name
        obj.description = description
        obj.owner_id = owner_id
        obj.creator_id = owner_id

        return self.save_item(obj)


class TableService(BaseService):
    def __init__(self):
        self.klass = TableModel

    def get_list(self, owner_id):
        """ get available project list """

        return self.klass.query.filter(
            self.klass.owner_id == owner_id,
        )

    def get_detail(self, owner_id, table_info):
        """ get available project list """

        if isinstance(table_info, int):
            # find table_id by id
            return self.klass.query.filter(and_(
                self.klass.id == table_info,
                self.klass.owner_id == owner_id,
            )).first()
        else:
            # find table_id by name
            return self.klass.query.filter(and_(
                self.klass.name == table_info,
                self.klass.owner_id == owner_id,
            )).first()

    def create(self, name, description, owner_id, proj_info):
        """ add new table """

        # find proj_info by proj_name
        if isinstance(proj_info, int):
            proj_id = proj_info
        else:
            psvc = ProjectService()
            proj_id = psvc.name_to_id(proj_info)
            if not proj_id:
                # if can not find existing project, add new one
                if psvc.create(proj_info, '', owner_id):
                    proj_id = psvc.name_to_id(proj_info)

        if not proj_id:
            return False

        # save data into database
        obj = self.klass()
        obj.name = name
        obj.description = description
        obj.proj_id = proj_id
        obj.owner_id = owner_id
        obj.creator_id = owner_id

        return self.save_item(obj)


class ColumnService(BaseService):
    def __init__(self):
        self.klass = ColumnModel

    def get_list(self, table_info):
        """ get available project list """

        if isinstance(table_info, int):
            table_id = table_info
        else:
            table_id = TableService().name_to_id(table_info)
            if not table_id:
                return False

        return self.klass.query.filter(
            self.klass.table_id == table_id
        )

    def get_detail(self, table_info, column_id):
        """ get available project list """

        if isinstance(table_info, int):
            table_id = table_info
        else:
            table_id = TableService().name_to_id(table_info)
            if not table_id:
                return False

        return self.klass.query.filter(and_(
            self.klass.id == column_id,
            self.klass.table_id == table_id,
        )).first()

    def create(self, name, description, owner_id, table_info, data={}):
        """ add new table """

        if data is None:
            return False
        # find table_id by table_name
        if isinstance(table_info, int):
            table_id = table_info
        else:
            table_id = TableService().name_to_id(table_info)
            if not table_id:
                return False

        # save data into database
        obj = self.klass(
            name=name,
            description=description,

            label=data['label'] if hasattr(data, 'label') else '',
            external_name=data['external_name'] if hasattr(
                data, 'external_name') else '',
            src_table=data['src_table'] if hasattr(data, 'src_table') else '',
            src_col=data['src_col'] if hasattr(data, 'src_col') else '',
            src_type=data['src_type'] if hasattr(data, 'src_type') else '',
            biz_category=data['biz_category'] if hasattr(
                data, 'biz_category') else '',
            logic_type=data['logic_type'] if hasattr(
                data, 'logic_type') else '',
            comments=data['comments'] if hasattr(data, 'comments') else '',

            table_id=table_id,
            creator_id=owner_id,
        )

        return self.save_item(obj)

    def import_table_schema(self, table_info, db_name, src_table, creator_id=0):
        # find table_id by table_name
        if isinstance(table_info, int):
            table_id = table_info
        else:
            table_id = TableService().name_to_id(table_info)
            if not table_id:
                return False

        clause = """
            insert into :des_table(n_inuse, d_create, c_name, c_label, c_src_tab, c_src_col, c_src_type, n_table_id, n_creator_id)
            select
                1 as n_inuse,
                now() as d_create,
                column_name as c_name,
                column_name as c_label,
                concat(table_schema,'.',table_name) as c_src_tab,
                column_name as c_src_col,
                case
                    when udt_name in('varchar', '_varchar', 'char', '_char', 'text', '_text') then udt_name || '(' || character_maximum_length || ')'
                    when udt_name in('int1', 'int2', 'int4', 'int8') then 'int'
                    else udt_name
                end as c_src_type,
                :table_id as n_table_id,
                :creator_id as n_creator_id
            from information_schema.columns
            where table_catalog=:db_name and table_schema='public'
                and table_name =:src_table
            order by table_name, ordinal_position;"""
        return self.execute_read_sql(clause, {
            'des_table': ColumnModel.__tablename__,
            'table_id': table_id,
            'db_name': db_name,
            'src_table': src_table,
            'creator_id': creator_id,
        })
