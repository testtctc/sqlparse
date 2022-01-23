# encoding=utf-8

import pytest

import sqlparse


def test_parser_empty():
    sql = ''' select * from foo where id in (select id from bar);
    select * from abtest limit 3'''
    print(sqlparse.format(sql, reindent=True, keyword_case='upper'))
    assert 1==1
