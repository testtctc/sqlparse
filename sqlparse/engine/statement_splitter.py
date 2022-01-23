#
# Copyright (C) 2009-2020 the sqlparse authors and contributors
# <see AUTHORS file>
#
# This module is part of python-sqlparse and is released under
# the BSD License: https://opensource.org/licenses/BSD-3-Clause

from sqlparse import sql, tokens as T


class StatementSplitter:
    """
    语句切割
    Filter that split stream at individual statements"""

    def __init__(self):
        self._reset()

    def _reset(self):
        """
        恢复原始状态
        Set the filter attributes to its default values"""
        self._in_declare = False
        self._is_create = False
        self._begin_depth = 0
        #消费空白
        self.consume_ws = False
        #token集合
        self.tokens = []
        self.level = 0

    def _change_splitlevel(self, ttype, value):
        """
        获取切割等级
        Get the new split level (increase, decrease or remain equal)"""

        # parenthesis increase/decrease a level
        if ttype is T.Punctuation and value == '(':
            return 1
        elif ttype is T.Punctuation and value == ')':
            return -1
        elif ttype not in T.Keyword:  # if normal token return
            return 0

        # Everything after here is ttype = T.Keyword
        # Also to note, once entered an If statement you are done and basically
        # returning
        unified = value.upper()

        # three keywords begin with CREATE, but only one of them is DDL
        # DDL Create though can contain more words such as "or replace"
        if ttype is T.Keyword.DDL and unified.startswith('CREATE'):
            self._is_create = True
            return 0

        # can have nested declare inside of being...
        if unified == 'DECLARE' and self._is_create and self._begin_depth == 0:
            self._in_declare = True
            return 1

        if unified == 'BEGIN':
            self._begin_depth += 1
            if self._is_create:
                # FIXME(andi): This makes no sense.
                return 1
            return 0

        # Should this respect a preceding BEGIN?
        # In CASE ... WHEN ... END this results in a split level -1.
        # Would having multiple CASE WHEN END and a Assignment Operator
        # cause the statement to cut off prematurely?
        if unified == 'END':
            self._begin_depth = max(0, self._begin_depth - 1)
            return -1

        if (unified in ('IF', 'FOR', 'WHILE', 'CASE')
                and self._is_create and self._begin_depth > 0):
            return 1

        if unified in ('END IF', 'END FOR', 'END WHILE'):
            return -1

        # Default
        return 0

    def process(self, stream):
        """
        处理流
        逻辑：碰到切割点则进一步，负责退一步
        Process the stream"""
        #结束标志服
        EOS_TTYPE = T.Whitespace, T.Comment.Single

        # Run over all stream tokens
        for ttype, value in stream:
            # Yield token if we finished a statement and there's no whitespaces
            # It will count newline token as a non whitespace. In this context
            # whitespace ignores newlines.
            # why don't multi line comments also count?
            if self.consume_ws and ttype not in EOS_TTYPE:
                #产生一段语句
                yield sql.Statement(self.tokens)

                # Reset filter and prepare to process next statement
                self._reset()

            # Change current split level (increase, decrease or remain equal)
            self.level += self._change_splitlevel(ttype, value)

            # Append the token to the current statement
            # 建立token
            self.tokens.append(sql.Token(ttype, value))

            # Check if we get the end of a statement
            if self.level <= 0 and ttype is T.Punctuation and value == ';':
                #结束
                self.consume_ws = True

        # Yield pending statement (if any)
        # 剩余的无法再匹配的token,单独成为语句
        if self.tokens and not all(t.is_whitespace for t in self.tokens):
            yield sql.Statement(self.tokens)
