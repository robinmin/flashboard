import math
from flashboard.utils import *

###############################################################################
#
# To run the test, please use the folowing command:
#     poetry run pytest -s tests/test_utility.py
#
###############################################################################


def test_generate_random_salt():
    # start test case
    for byte_size in [64, 128, 17]:
        result = generate_random_salt(byte_size)
        # print('base64({}) -> {}'.format(byte_size, 4 * math.ceil(byte_size/3)))
        assert result is not None and len(result) == 4 * math.ceil(byte_size/3),\
            'Length({}) : {} != {}'.format(
            byte_size,
            len(result),
            4 * math.ceil(byte_size/3)
        )


def test_as_map():
    # build test data
    td = [
        {'name': 'Abe', 'age': 55, 'day_of_birth': '2018-10-01'},
        {'name': 'Yokohama', 'age': 24, 'day_of_birth': '2020-10-01'},
        {'name': 'Yamazaki', 'age': 70},
        {'name': 'Maeda', 'age': 6, 'day_of_birth': '2012-10-01'},
    ]

    # start test case
    result = as_map(None, None, None)
    assert result is None, 'Return None when all input is None'

    result = as_map(None, '', None)
    assert result is None, 'Return None when key_name is blank( and dataset is None)'

    result = as_map(td, '', None)
    assert result is None, 'Return None when key_name is blank( and dataset is not None)'

    result = as_map(td, 'name', 'age')
    key_str = ','.join(sorted(result.keys()))
    val_str = ','.join([
        str(idx) for idx in sorted(result.values()
                                   )])
    assert result is not None \
        and len(result) == len(td)\
        and key_str == 'Abe,Maeda,Yamazaki,Yokohama'\
        and val_str == '6,24,55,70', 'get map succefully(string -> integer)'

    result = as_map(td, 'age', 'name')
    key_str = ','.join([
        str(idx) for idx in sorted(result.keys()
                                   )])
    val_str = ','.join(sorted(result.values()))
    assert result is not None \
        and len(result) == len(td)\
        and key_str == '6,24,55,70'\
        and val_str == 'Abe,Maeda,Yamazaki,Yokohama', 'get map succefully(integer -> string)'

    result = as_map(td, 'name', 'day_of_birth')
    key_str = ','.join(sorted(result.keys()))
    val_str = ','.join(
        [str(idx) if idx is not None else '' for idx in result.values()])
    # print(key_str)
    # print(val_str)
    assert result is not None \
        and len(result) == len(td)\
        and key_str == 'Abe,Maeda,Yamazaki,Yokohama'\
        and val_str == '2018-10-01,2020-10-01,,2012-10-01', 'get map succefully with None value(string -> string)'

    result = as_map(td, 'day_of_birth', 'name')
    key_str = ','.join(sorted(result.keys()))
    val_str = ','.join(
        [str(idx) if idx is not None else '' for idx in sorted(result.values())])
    # print(key_str)
    # print(val_str)
    assert result is not None \
        and len(result) == len(td) - 1\
        and key_str == '2012-10-01,2018-10-01,2020-10-01'\
        and val_str == 'Abe,Maeda,Yokohama', 'get map succefully with None key(string -> string)'
