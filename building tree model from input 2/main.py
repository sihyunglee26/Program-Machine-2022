import argparse
import command

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='-c filename')
    
    parser.add_argument('-c', help='input file that describes usable commands', default='command-1-line.txt')

    args = parser.parse_args()
    print(args)
        
    expressions = command.read_file(args.c)     # parse expressions

    # display each parsed expressions
    for i in expressions:
        print(str(i)+':')
        print(expressions[i].toString())
        print()

    # create a single tree that combines all expressions
    tree = command.deepcopyExpression(expressions['e0'], 0, 20)
    #print(tree.toString())
