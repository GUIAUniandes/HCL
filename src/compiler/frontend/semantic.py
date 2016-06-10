# -*- coding: utf-8 -*-

from __future__ import print_function

import vm
import os
import re
import sys
import parser

basepath = os.path.dirname(__file__)
INFERENCE_PATH = '../../../doc/language/Inference_Rules.txt'
INFERENCE_PATH = os.path.abspath(os.path.join(basepath, INFERENCE_PATH))

VAR = u'VAR'
OP = u'name'
COMMA = u'comma'
ARRAY = u'ARRAY'
NUM = u'number'
COMMA = u'comma'
DO = u'DO'
GUARD_SEP = u'guard_sep'
GUARD_EXEC = u'guard_exec'
INT = u'int'
BOOLEAN = u'boolean'
CHAR = u'char'
FUNC = u'func'
READ = u'read'
LSPAREN = u'left_sparen'
LRPAREN = u'left_rparen'
INF = u'infty'

NEXPR = u'E'
FEXPR = u'C'

# operators = []
inference = {'single':{}, 'double':{}}
count = {'if':0, 'do':0, 'addr':0, 'lvl':-1, 'index':0, 'func':0}

VM_TYPES = {'INTEGER':INT, 'BOOLEAN':BOOLEAN, 'CHAR':CHAR}

def analyse(path):
    # global operators
    tree, status_code = parser.parse(path)
    if status_code != 0:
       print("Compiler exited with status %d" % (status_code), file=sys.stderr)
       return None, status_code
    lvl = -1
    scope = {}
    definitions = {}
    program = {}
    guards = {}
    instructions = {}
    func = {}
    addresses = {}
    indices = {}
    data = {'path':path, 'scope':scope, 'definitions': definitions,
            'program': program, 'guards':guards, 'instructions':instructions,
            'functions':func, 'addresses':addresses, 'indices':indices}
    root = tree
    node = tree.children[3]

    with open(INFERENCE_PATH, 'rb') as fp:
         lines = fp.readlines()

    for line in lines:
        line = line.strip('\n')
        op,args = line.split(' : ')
        ty,res = args.split(' -> ')
        t = ty.split(' x ')
        if len(t) > 1:
           t1, t2 = t
           ops = inference['double']
        elif len(t) == 1:
           ops = inference['single']
        try:
          info = ops[op]
        except KeyError:
          info = {}
          ops[op] = info
        if len(t) > 1:
           try:
             op_res = info[t1]
           except KeyError:
             op_res = {}
             info[t1] = op_res
           op_res[t2] = res
           try:
             op_res = info[t2]
           except KeyError:
             op_res = {}
             info[t2] = op_res
           op_res[t2] = res
        else:
           info[t[0]] = res
        # operators.append(op)
    # operators = list(set(operators)) 

    # status_code, node = analyse_tree(node, root, data)



def process_expr(node, data, lvl, _type=None):
    #Node: Start of Expression 
    stat = 0
    addr = None
    typ = None
    if not isinstance(data, dict):
       raise Exception("a")
    operators = set(inference['double'].keys()).union(inference['single'].keys())
    exprs = expr_str(node, operators)
    print(exprs)
    operator = {'var':None, 'func':None, 'addr':None, 'index':None, 'type':None, 'num':None}
    op = {'oper1':None, 'op':None, 'oper2':None}
    if node.value.token == OP:
       stat, typ = process_var(node, operator, exprs, data, lvl)
       op['oper1'] = operator
       addr = 'addr%d' % (count['addr'])
       data['addresses'][addr] = op
       count['addr'] += 1
    elif node.value.token == FUNC:
       stat, typ = process_func(node, operator, exprs, data, lvl)
       op['oper1'] = operator
       addr = 'addr%d' % (count['addr'])
       data['addresses'][addr] = op
       count['addr'] += 1
    elif node.value.token == NUM or node.value.token == INF:
       typ = INT
       operator['num'] = node.value
       op['oper1'] = operator
       addr = 'addr%d' % (count['addr'])
       data['addresses'][addr] = op
       count['addr'] += 1
    elif node.value.token in operators:
       stat, typ = process_operand(node, op, exprs, data, lvl)
       addr = 'addr%d' % (count['addr'])
       data['addresses'][addr] = op
       count['addr'] += 1
    if stat == 0:
       if _type is not None:
          if _type != typ:
             stat = -8
             print("File: %s - Line: %d:%d\nType Mismatch: Expression %s must be of type %s, got: %s" % (data['path'], node.value.line, node.value.col, exprs, _type, typ), file=sys.stderr)
    return stat, typ, addr           

def process_operand(node, op, exprs, data, lvl):
    if not isinstance(data, dict):
       raise Exception("a")
    stat = 0
    typ = None
    addr = None
    op['op'] = node.value
    op_ret = []
    pointers = []
    for operand in node.children:
        stat, operand_type, operand_addr = process_expr(operand, data, lvl)
        if stat != 0:
           break
        op_ret.append(operand_type)
        pointers.append(operand_addr)
    if stat == 0:
       if len(op_ret) == 1:
          try:
            typ = inference['single'][node.value.token][op_ret[0]]
            op['oper2'] = {'var':None, 'func':None, 'addr':pointers[0], 'index':None, 'type':None, 'num':None}
          except KeyError:
            stat = -10
            print(u"File: %s - Line: %d:%d\nDimension Mismatch: Expression: %s - Operator %s is not defined for argument of type %s; Expected: %s" % (data['path'], node.value.line, node.value.col, exprs, node.value.value, op_ret[0], ', '.join(inference['single'][node.value.token].keys())), file=sys.stderr)
       elif len(op_ret) == 2:
          try:
            typ = inference['double'][node.value.token][op_ret[0]][op_ret[1]]
            op['oper1'] = {'var':None, 'func':None, 'addr':pointers[0], 'index':None, 'type':None, 'num':None}
            op['oper2'] = {'var':None, 'func':None, 'addr':pointers[1], 'index':None, 'type':None, 'num':None}
          except KeyError:
            stat = -10
            opt = ', '.join(reduce(lambda u,v:u+v, [map(lambda y: u'('+x+', '+y+')', semantic.inference['double'][node.value.token]) for x in semantic.inference['double'][node.value.token]]))
            print(u"File: %s - Line: %d:%d\nDimension Mismatch: Expression: %s - Operator %s is not defined for arguments of type (%s, %s); Expected: %s" % (data['path'], node.value.line, node.value.col, exprs, node.value.value, op_ret[0], op_ret[1], opt), file=sys.stderr)       
    return stat, typ

def process_var(node, operator, exprs, data, lvl):
    if not isinstance(data, dict):
       raise Exception("a")
    stat, typ, shp, scope = lookup_var(node.value, data, lvl)
    if stat == 0:
       operator['var'] = {'scope':scope, 'var':node.value}
       if len(shp) == len(node.children):
          if len(shp) > 0:
             stat, idx = process_indices(node.children, data, lvl)
             operator['index'] = idx
       else:
          stat = -7
          print("File: %s - Line: %d:%d\nDimension Mismatch: Expression: %s - Variable must be referenced with %d indices, got %d" % (data['path'], node.value.line, node.value.col, exprs, len(shp), len(node.children)), file=sys.stderr)
    return stat, typ

def process_func(node, operator, exprs, data, lvl):
    if not isinstance(data, dict):
       raise Exception("a")
    #Node: Function call
    stat = 0
    func_call = {'call':None, 'args':[]}
    typ = None
    func_name = node.value.value.split('(')[0]
    arg_types = []
    func_desc = []
    try:
      func_desc = vm.atomic.TYPES[vm.hardware.ATOMIC[func_name]]
    except KeyError:
      stat = -9
      print("File: %s - Line: %d:%d\nUndefined Function: Expression: %s - Function %s must be defined" % (data['path'], node.value.line, node.value.col, exprs, func_name), file=sys.stderr)
    if stat == 0:
       args = []
       in_types = []
       for arg in node.children:
           stat, arg_type, pointer = process_expr(arg, data, lvl)
           if stat != 0:
              break
           args.append(pointer)
           in_types.append(arg_type)
       if stat == 0:
          matches = 0
          found = False
          impl = ', '.join(['('+', '.join([VM_TYPES[j] for j in opt[0]])+')'+':'+VM_TYPES[opt[1]] for opt in func_desc])
          for opt in func_desc:
              out_typ = VM_TYPES[opt[1]]
              if len(args) == len(opt[0]):
                 for i in range(0, len(args)):
                     if in_types[i] == VM_TYPES[opt[0][i]]:
                        matches += 1
                     else:
                        matches = 0
                        break
              if matches == len(args):
                 typ = out_typ
                 found = True
                 break
          if not found:
             stat = -9
             print("File: %s - Line: %d:%d\nFunction Arguments Type Mismatch: Expression: %s - Function %s is not defined for arguments: %s; Expected: %s" % (data['path'], node.value.line, node.value.col, exprs, func_name, '('+', '.join(in_types)+')', impl), file=sys.stderr)
          else:
             func_call['call'] = func_name
             func_call['args'] = args
             idx = 'func%d' % (count['func'])
             count['func'] += 1
             data['functions'][idx] = func_call
             operator['func']= idx
    return stat, typ             


def process_indices(children, data, lvl):
    indices = []
    for index in children:
        stat, _, pointer = process_expr(index, data, lvl, _type=INT)
        if stat != 0:
           break
        indices.append(pointer)
    idx = 'index%d' % (count['index'])
    data['indices'][idx] = indices 
    count['index'] += 1
    return stat, idx 

def lookup_var(tok, data, lvl):
    stat = 0
    inf = None
    # print(tok)
    # print(lvl)
    # print(data)
    name = tok.value
    typ = None
    shp = -1
    while lvl != -1:
       try:
         # print(data['definitions'])
         inf = data['definitions'][lvl][name]
         break
       except KeyError:
         lvl = data['scope'][lvl]['inside']
    if not inf:
       stat = -6
       print("File: %s - Line: %d:%d\nUndefined Variable: Variable %s must be defined" % (data['path'], tok.line, tok.col, name), file=sys.stderr)
    else:
       typ = inf['type']
       shp = inf['size']
    return stat, typ, shp, lvl


def process_definition(child, data, lvl):
    #Child: Sibling of VAR
    scope = data['definitions']
    stat = 0
    limit = child.next
    node = child
    variables = []
    while id(node) != id(limit):
       if len(node.children) > 0:
          node = node.children[0]
       else:
          if node.value != '':
             if node.value.token == OP:
                variables.append(node.value)
          node = node.up_node()
    node = limit.next
    node = node.children[0]
    if node.value is not None:
       if node.value.token == ARRAY:
          node = node.next.children[1]
          limit = node.next
          val_1 = None
          val_tok = None
          val_2 = None
          shape = []
          while id(node) != id(limit):
             if len(node.children) > 0:
                node = node.children[0]
             else:
                if node.value != '':
                   if node.value.token == NUM:
                      if val_1 is None:
                         val_1 = int(node.value.value)
                         val_tok = node
                      else:
                         val_2 = int(node.value.value)
                   elif node.value.token == COMMA:
                      length = val_2-val_1+1
                      if length < 0:
                         stat = -5
                         print("File: %s - Line: %d:%d\nIndex Error: Invalid array initialization interval [%d, %d], length must be positive" % (data['path'], val_tok.value.line, val_tok.value.col, val_1, val_2), file=sys.stderr)
                         val_1 = None
                         val_tok = None
                         val_2 = None
                         break
                      else:
                         val_1 = None
                         val_tok = None
                         val_2 = None
                         shape.append(length)
                node = node.up_node()
          if val_1 != None:
             length = val_2-val_1+1
             if length < 0:
                stat = -5
                print("File: %s - Line: %d:%d\nIndex Error: Invalid array initialization interval [%d, %d], length must be positive" % (data['path'], val_tok.value.line, val_tok.value.col, val_1, val_2), file=sys.stderr)   
             else:
                shape.append(length)
          node = node.up_node()
          node = node.next
          type_tok = node.children[0].value.value
    else:
       type_tok = node.children[0].value.value
       shape = []
    if stat == 0:
       try:
         info = scope[lvl]
       except KeyError:
         info = {}
         scope[lvl] = info
       for var in variables:       
           info[var.value] = {'size':shape, 'type':type_tok, 'tok':var}
    return stat, node.up_node()

def expr_str(node, operators, operator=False, s=u''):
    app = u'%s'
    if node.value.token in operators:
       if operator:
          app = u'(%s)'
       if len(node.children) > 1:
          s += app % (node.value.value.join(map(lambda x: expr_str(x, operators, True, ''), node.children)))
       else:
          app = node.value.value+u'%s'
          s += app % (expr_str(node.children[0], operators, True, ''))
    elif node.value.token == u'func':
       s += node.value.value+u','.join(map(lambda x: expr_str(x, operators, False, ''), node.children))+u')'
    elif node.value.token == u'name':
       s += node.value.value
       if len(node.children) > 0:
          s += u'['+(u','.join(map(lambda x: expr_str(x, operators, False, ''), node.children)))+u']'
    else:
       s += node.value.value
    return s

