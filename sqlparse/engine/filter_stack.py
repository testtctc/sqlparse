#
# Copyright (C) 2009-2020 the sqlparse authors and contributors
# <see AUTHORS file>
#
# This module is part of python-sqlparse and is released under
# the BSD License: https://opensource.org/licenses/BSD-3-Clause

"""filter"""

from sqlparse import lexer
from sqlparse.engine import grouping
from sqlparse.engine.statement_splitter import StatementSplitter


class FilterStack:
    def __init__(self):
        #预处理
        self.preprocess = []
        #语句处理
        self.stmtprocess = []
        #后续处理
        self.postprocess = []
        #是否聚合
        self._grouping = False

    def enable_grouping(self):
        self._grouping = True

    def run(self, sql, encoding=None):
        """处理流程"""
        #分词
        stream = lexer.tokenize(sql, encoding)
        # Process token stream

        #预先处理
        for filter_ in self.preprocess:
            stream = filter_.process(stream)

        #语句切割
        stream = StatementSplitter().process(stream)

        # Output: Stream processed Statements
        for stmt in stream:
            if self._grouping:
                #合并token
                stmt = grouping.group(stmt)
            #处理当前语句
            for filter_ in self.stmtprocess:
                filter_.process(stmt)
            #后续处理
            for filter_ in self.postprocess:
                stmt = filter_.process(stmt)
            #返回语句
            yield stmt
