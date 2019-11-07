from knowall.models import ColumnModel
from knowall.services import ProjectService, TableService, ColumnService
###############################################################################


def test_create_project(app):
    psvc = ProjectService()

    # add new project normally
    count_before = psvc.count()
    result = psvc.create(
        'test-project2',
        'This is a demo description on the test-project2',
        1
    )
    count_after = psvc.count()
    assert result and count_before + \
        1 == count_after, 'Failed to add new project normally'

    # add duplicated project
    count_before = psvc.count()
    result = psvc.create(
        'test-project2',
        'This is a demo description on the test-project2',
        1
    )
    count_after = psvc.count()
    assert not result and count_before == count_after, 'Failed to add duplicated project'


# def test_create_table(app):
#     psvc = ProjectService()
#     tsvc = TableService()

#     # add new table normally (new project)
#     proj_count_before = psvc.count()
#     tab_count_before = tsvc.count()
#     result = tsvc.create(
#         'test-table2',
#         'This is a demo description on the test-table2',
#         1,
#         'test-project'
#     )
#     proj_count_after = psvc.count()
#     tab_count_after = tsvc.count()
#     assert result \
#         and proj_count_before + 1 == proj_count_after\
#         and tab_count_before + 1 == tab_count_after, 'Failed to add new table normally (new project)'

#     # add duplicated table
#     proj_count_before2 = psvc.count()
#     tab_count_before2 = tsvc.count()
#     result = tsvc.create(
#         'test-table2',
#         'This is a demo description on the test-table2',
#         1,
#         'test-project'
#     )
#     proj_count_after2 = psvc.count()
#     tab_count_after2 = tsvc.count()
#     assert not result \
#         and proj_count_before2 == proj_count_after2\
#         and tab_count_before2 == tab_count_after2, 'Failed to add duplicated table'

#     # add new table normally (existing project)
#     proj_count_before3 = psvc.count()
#     tab_count_before3 = tsvc.count()
#     result = tsvc.create(
#         '2nd-table',
#         'This is a demo description on the 2nd-table',
#         1,
#         'test-project'
#     )
#     proj_count_after3 = psvc.count()
#     tab_count_after3 = tsvc.count()
#     assert result \
#         and proj_count_before3 == proj_count_after3\
#         and tab_count_before3 + 1 == tab_count_after3, 'Failed to add new table normally (existing project)'


def test_create_column(app):
    csvc = ColumnService()

    col_count_before = csvc.count()
    result = csvc.create(
        'col_01',
        'Column 01',
        1,
        'test-table',
        {
            'name': 'c_col01',
            'label': 'character column 01',
            'src_table': 'test-table',
            'src_col': 'col01',
            'src_type': 'varchar(30) not null',
        }
    )
    col_count_after = csvc.count()
    assert result \
        and col_count_before + 1 == col_count_after, 'Failed to add new column normally (existing table)'

    # add duplicated column
    col_count_before2 = csvc.count()
    result = csvc.create(
        'col_01',
        'Column 01',
        1,
        'test-table',
        {
            'name': 'c_col01',
            'label': 'character column 01',
            'src_table': 'test-table',
            'src_col': 'col01',
            'src_type': 'varchar(30) not null',
        }
    )
    col_count_after2 = csvc.count()
    assert not result \
        and col_count_before2 == col_count_after2, 'Failed to add duplicated column (existing table)'


# def test_import_table_schema(app):
#     csvc = ColumnService()

#     col_count_before = csvc.count()
#     result = csvc.import_table_schema(
#         'test-table',
#         'flashboard',
#         ColumnModel.__tablename__,
#         1
#     )
#     col_count_after = csvc.count()
#     assert result \
#         and col_count_before < col_count_after, 'Failed to add new column normally (existing table)'
