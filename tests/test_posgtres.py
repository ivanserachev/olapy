from __future__ import absolute_import, division, print_function

import os
import pandas as pd
import pytest
from pandas.util.testing import assert_frame_equal


from tests.queries import query_posgres1, query_posgres2, query_postgres3

CUBE = 'sales_postgres'

def test_conf_file_change():
    from olapy.core.mdx.executor.execute import MdxEngine
    with open(os.path.join(MdxEngine._get_default_cube_directory(),'olapy-config.xml'), "w") as f:
        f.write("""
        <!-- this config file will be deleted ASAP -->
        <olapy>
            <database>
                <sgbd>postgres</sgbd>
                <user_name>postgres</user_name>
                <password>root</password>
                <host>localhost</host>
                <port>5432</port>
            </database>
        </olapy>
        """)


@pytest.fixture(scope='module')
def executor():
    from olapy.core.mdx.executor.execute import MdxEngine
    return MdxEngine(CUBE)

def test_execution_query1(executor):
    executor.mdx_query = query_posgres1

    df = executor.execute_mdx()['result']
    test_df = pd.DataFrame({
        'country': ['France', 'Spain', 'Switzerland', 'United States'],
        'amount': [4, 3, 248, 768],
    }).groupby(['country']).sum()

    assert assert_frame_equal(df, test_df) is None


def test_execution_query2(executor):
    executor.mdx_query = query_posgres2

    df = executor.execute_mdx()['result']
    test_df = pd.DataFrame({
        'year': [
            2010, 2010, 2010, 2010, 2010, 2010, 2010, 2010, 2010, 2010, 2010,
            2010, 2010
        ],
        'quarter': [
            -1, 'Q2 2010', 'Q2 2010', 'Q2 2010', 'Q2 2010', 'Q2 2010',
            'Q2 2010', 'Q2 2010', 'Q2 2010', 'Q2 2010', 'Q2 2010', 'Q2 2010',
            'Q2 2010'
        ],
        'month': [
            -1, -1, 'May 2010', 'May 2010', 'May 2010', 'May 2010', 'May 2010',
            'May 2010', 'May 2010', 'May 2010', 'May 2010', 'May 2010',
            'May 2010'
        ],
        'day': [
            -1, -1, -1, 'May 12,2010', 'May 13,2010', 'May 14,2010',
            'May 15,2010', 'May 16,2010', 'May 17,2010', 'May 18,2010',
            'May 19,2010', 'May 20,2010', 'May 21,2010'
        ],
        'amount': [1023, 1023, 1023, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
    }).groupby(['year', 'quarter', 'month', 'day']).sum()

    assert assert_frame_equal(df, test_df) is None



def test_execution_query10(executor):
    executor.mdx_query = query_postgres3

    df = executor.execute_mdx()['result']
    test_df = pd.DataFrame({
        'year': [2010, 2010, 2010, 2010, 2010, 2010, 2010, 2010],
        'quarter': [
            'Q2 2010', 'Q2 2010', 'Q2 2010', 'Q2 2010', 'Q2 2010', 'Q2 2010',
            'Q2 2010', 'Q2 2010'
        ],
        'month': [
            'May 2010', 'May 2010', 'May 2010', 'May 2010', 'May 2010',
            'May 2010', 'May 2010', 'May 2010'
        ],
        'day': [
            'May 19,2010',
            'May 17,2010',
            'May 15,2010',
            'May 13,2010',
            'May 12,2010',
            'May 14,2010',
            'May 16,2010',
            'May 18,2010',
        ],
        'continent': [
            'Europe', 'Europe', 'Europe', 'Europe', 'Europe', 'Europe',
            'Europe', 'Europe'
        ],
        'count': [13, 65, 231, 841, 84, 2, 4, 64]
    }).groupby(
        ['year', 'quarter', 'month', 'day', 'continent'], sort=False).sum()

    assert assert_frame_equal(df, test_df) is None
