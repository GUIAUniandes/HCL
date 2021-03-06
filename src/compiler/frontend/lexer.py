# -*- coding: utf-8 -*-

from __future__ import print_function

import re
import os
import sys
import codecs

regex = {'comma':'^[,]$', 'semicolon':'^[;]$', 'colon':'^[:]$', 'slice':'^[.][.]$', 'name':r'^[a-zA-Z_]\w*$',
         'number':r'^\d+$', 'eq':r'^[=]$', 'leq':u'^≤$', 'geq':u'^≥$',
         'le':r'^[<]$', 'ge':r'^>$', 'plus':r'^[+]$', 'minus':'^[-]$', 'times':'^[*]$', 'mod':'^[%]$',
         'div':'^[/]$', 'neq':u'^≠$', 'not':u'^¬$', 'and':u'^∧$', 'or':u'^∨$', 'in':u'^∈$',
         'not_in':u'^∉$', 'union':u'^∪$', 'intersection':u'^∩$', 'infty':u'^∞$',
         'empty':u'^∅$', 'guard_sep':u'^□$', 'left_rparen':r'^[(]$',
         'right_rparen':r'^[)]$', 'left_sparen':r'^[[]$', 'right_sparen':r'^[]]$',
         'assignment':u'^←$', 'guard_exec':u'^→$', 'comment':r'[{].*', 'power':r'^\^$',
         'func':r'^[a-zA-Z_]\w*[(]$', 'character':r'^["][\\]?[a-zA-Z0-9_!"#$%&/()=?\'\-+\*\[\]\{\}/~\^@,.:;<>|¬` ]["]$'}

keywords = {'program':'PROGRAM', 'begin':'BEGIN' ,'if':'IF', 'fi':'FI', 'begin':'BEGIN', 'end':'END', 'do':'DO', 'od':'OD',
            'for':'FOR', 'rof':'ROF', 'abort':'ABORT', 'skip':'SKIP', 'array':'ARRAY',
            'of':'OF', 'var':'VAR', 'int':'INT', 'integer':'INT', 'boolean':'BOOLEAN', 'print':'PRINT', 'char' : 'CHAR',
            'read(':'READ', 'true':'true', 'false':'false'}

class Token(object):
   def __init__(self, token, value, l=0, col=0):
       self.token = token
       self.value = value
       self.line = l
       self.col = col

   def __unicode__(self):
       return u'<'+self.token+u', '+self.value+u'>'

   def __str__(self):
       return self.__unicode__().encode('utf-8')

   def __repr__(self):
       return self.__str__()

   def __eq__(self, y):
       if not isinstance(y, Token):
          return False
       return self.token == y.token

   def __neq__(self, y):
       if not isinstance(y, Token):
          return True
       return not self.token == y.token

   def __hash__(self):
       return hash(self.token)


def remove_trailing_spaces(s):
    init_idx = None
    end_idx = 0
    for i,c in enumerate(s):
        if len(re.findall('\s', c)) > 0:
           pass
        else:
           if init_idx is None:
              init_idx = i
           else:
              end_idx = i
    comp = ''
    if init_idx is not None:
       comp = s[init_idx:end_idx+1]
    return comp

def lex(lines, filename):
    status_code = 0
    tokens = []
    for lc, line in enumerate(lines):
        word = ''
        i = 0
        last_id = None
        while i < len(line):
            c = line[i]
            if len(re.findall('\S', c)) > 0:
               word += c
               match_found = False
               for name in regex:
                   if len(re.findall(regex[name], word)) > 0:
                      match_found = True
                      break
               if match_found:
                  if name == 'name' or name == 'func':
                     try:
                        last_id = keywords[word]
                     except KeyError:
                        last_id = name
                  elif name == 'comment' or name == 'semicolon':
                     break
                  else:
                     last_id = name
               else:
                  if last_id is not None:
                     word = word[:-1]
                     tokens.append(Token(last_id, word, lc+1, i+1))
                     word = ''
                     last_id = None
                     i -= 1
                  else:
                     if word != '.':
                        fault = True
                        if '"' in word:
                           increm = 3
                           if i+1 <= len(line):
                              if line[i+1] == '\\':
                                 increm = 4
                           word = line[i:i+increm]
                           # print(word)
                           if len(re.findall(regex['character'], word)) > 0:
                              tokens.append(Token('character', word, lc+1, i+1))
                              fault = False
                              word = ''
                              last_id = None
                              i += increm+1 
                           else:
                              word = line[i]
                        if fault:
                           print("File: %s - Line: %d:%d\nSyntax Error: Unrecognized or invalid symbol: %s" % (filename, lc+1, i+1, word), file=sys.stderr)
                           status_code = -1
            else:
               if last_id is not None:
                  tokens.append(Token(last_id, word, lc+1, i+1))
               word = ''
               last_id = None
            i += 1
    return status_code, tokens



