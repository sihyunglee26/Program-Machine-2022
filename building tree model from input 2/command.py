import re
import warnings

# type of expressions
STRING = 1
EXPRESSION = 2
ANDED = 3
ORED = 4

expressions = dict()                    # dictionary that stores parsed expressions
p = re.compile('e[0-9]+')           # regex for an expression (e.g., "e3")
p_d = re.compile('e[0-9]+:\n')      # regex for the definition of an expression  (e.g., "e3:")

'''
read Input #2 from a file,
parse expressions,
and store parsed expressions in the dictionary "expressions"
'''
def read_file(filename):
    fp = open(filename, "r")

    stage = -1
    eCurrent = None
    eCurrentOR = None
    eCurrentAND = None

    line = fp.readline()

    while line:        
        # remove comments, which begin with "#"
        comment_index = line.find('#')        
        if comment_index >= 0:
            line = line[:comment_index] + '\n'
        line = line.rstrip() + '\n' # remove trailing whitespaces. heading whitespaces remain since indentation is important in python
        
        #print("[" + line + "]")

        if p_d.fullmatch(line):         # definition (ex: "e1: ")
            stage = expressionNum(line)
            eCurrentOR = Expression()
            eCurrentOR.type = ORED
            eCurrentAND = Expression()
            eCurrentAND.type = ANDED
            eCurrentOR.OR.append(eCurrentAND)
            eCurrentOR.size += 1
            eName = expressionName(line)
            if eName in expressions:
                raise Exception('{} is defined more than once. Each expression must be defined only once.'.format(eName))
            expressions[eName] = eCurrentOR

        elif line != '\n':
            if eCurrentOR == None:  # e0 begins without "e0:"
                stage = 0
                eCurrentOR = Expression()
                eCurrentOR.type = ORED
                eCurrentAND = Expression()
                eCurrentAND.type = ANDED
                eCurrentOR.OR.append(eCurrentAND)
                eCurrentOR.size += 1
                expressions['e0'] = eCurrentOR
                
            if line.startswith('----'):
                eCurrentAND = Expression()
                eCurrentAND.type = ANDED
                eCurrentOR.OR.append(eCurrentAND)
                eCurrentOR.size += 1
                
            else:    
                parseCode(line, eCurrentAND)

        line = fp.readline()

    fp.close()
    return expressions

'''
class that represents an expression
'''
class Expression:
    def __init__(self, expressionString=None, expressionId=None, expressionType=STRING):
        self.type = expressionType              # string, exp, ANDED, ORED (default is string)
        self.size = 0                                         # number of tokens
        self.STR = expressionString
        self.EXP = expressionId
        self.AND = list()
        self.OR = list()
        self.OR_output_list = list()            # connect outputs that results from each selection
        
        self.descendents = list()       # used in orderORexpressions()
        self.ordered = False            
        
        self.selection_order = list()   # if selection == k, choose OR[selection_order[k]]
        self.selection = 0        
        self.parent = None        

    def currentSelection(self):
        return self.selection_order[self.selection]
        
    def toString(self):        
        if self.type == STRING:
            return self.STR
        elif self.type == EXPRESSION:
            return self.EXP
        elif self.type == ANDED:
            total = ''
            for a in self.AND:
                temp = a.toString()
                total += temp
                if temp[-1] != '\n':
                    total += ' '                
            return total[:-1]       # return except the last '\n'
            #print(total)
        elif self.type == ORED:
            total = ''
            if self.EXP:
                total += self.EXP + '\n'
            for o in self.OR[:-1]:                
                total += o.toString() + '\n----\n'
                #print(o.toString())
            total += self.OR[-1].toString() + '\n'
            return total[:-1]       # return except the last '\n'

'''
parse one line of Input #2
this function is called from within read_file()
'''
def parseCode(line, cursor):        # codeSketch 파싱하기. expression 파싱이랑 합쳐보기
    code = ''   # current buffer of consecutive non-expression tokens
    tokens = line.split(" ")
    prev_e = None

    cursor.type = ANDED
    for token in tokens:
        #print('[',token,']')
        token_s = token.strip() # last token in a line contains a trailing '\n', so remove it
        if p.fullmatch(token_s):  # recursive한 경우 (ex: 1 + e1)
            #print('[',token_s,']')
            if len(code) != 0:
                cursor.AND.append(Expression(expressionString=code))
                cursor.size += 1

            prev_e = Expression(expressionId=token_s, expressionType=EXPRESSION)
            cursor.AND.append(prev_e)
            cursor.size += 1
            if token[-1] == '\n':
                cursor.AND.append(Expression(expressionString='\n'))
                cursor.size += 1
            code = ''

        elif not code:          # code buffer is empty
            if len(token) == 0: # empty token means a space
                code += ' ' # indentation is important for python
            else:
                code += token

            prev_e = None
            
        else:                   # code buffer is NOT empty
            code += (' ' + token)
            prev_e = None
            
        #print(code)
        
    if len(code) != 0:  # 그렇지 않은 경우 (ex: input[i])
        cursor.AND.append(Expression(expressionString=code))
        cursor.size += 1


def expressionNum(line):        # eN일 경우 N return
    return int(line[1:-2])      # remove heading "e" and trailing ":\n"    


def expressionName(line):
    return line[:-2]            # remove trailing ":\n"    


'''
create a single tree that combines all expressions
    (1) begin with the tree of expression "e0"
    (2) search the tree with DFS            
    (3) if any expression object is encountered, replace it with the corresponding tree
    (4) repeat (2)-(3) until no more expresion object is found
the DFS search does not go into the tree deeper than "depthMax"
this is because an expression can be defined recursively by including itself in the definition
        and in such case, the search can go deeper infinitely
'''
selections = list()
def deepcopyExpression(e, depth=0, depthMax=None):      
    if depthMax != None and depth > depthMax:
        warnings.warn('tree reached its max depth. check to see whether depthMax needs to be increased in deepcopyExpression()')
        return None    
    elif e.type == STRING:
        return e
    elif e.type == EXPRESSION:
        if e.EXP not in expressions:
            raise Exception('{} is referred but not defined.'.format(e.EXP))
        cursor = deepcopyExpression(expressions[e.EXP], depth, depthMax)
        if (cursor == None):        # these two lines are added to accommodate the case where depth reached the maximum
            return None
        cursor.EXP = e.EXP        
        return cursor
    elif e.type == ANDED:
        cursor = Expression()
        cursor.type = ANDED
        for esub in e.AND:
            temp = deepcopyExpression(esub, depth+1, depthMax)
            if (temp == None):
                return None     # if any one term is nullified in ANDed expression, then entire ANDed expression is nullified
            temp.parent = cursor
            cursor.AND.append(temp)
            cursor.size += 1
        return cursor
    elif e.type == ORED:
        cursor = Expression()
        cursor.type = ORED
        for esub in e.OR:
            temp = deepcopyExpression(esub, depth+1, depthMax)
            if (temp != None):  # if one term is nullified in ORed expression, then this term is trashed, while others remain
                temp.parent = cursor
                cursor.OR.append(temp)
                cursor.size += 1
        if cursor.size > 0:
            selections.append(cursor)            
            return cursor
        else:
            return None
