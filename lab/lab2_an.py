import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ir import *
from codegen.cpu import *

def PrintCCode(ir):
	code = ''
	for d in ir:
		# if d:
			code += to_string(d)
	print(code)

def Loop0():
    ir = []

    L = Scalar('int', 'L')
    M = Scalar('int', 'M')
    N = Scalar('int', 'N')
    A = Ndarray('int', (N, M, L), 'A')
    B = Ndarray('int', (N, M, L), 'B')

    loopi = Loop(0, 20, 1, [])
    loopj = Loop(Expr(loopi.iterate, 3, '+'),  Expr(loopi.iterate, 10, '+'), 1, [])
    loopk = Loop(Expr(loopj.iterate, 20, '+'), Expr(loopj.iterate, 30, '+'), 1, [])

    loopi.body.append(loopj)
    loopj.body.append(loopk)

    lhs1 = Index(Index(Index(A, Expr(loopi.iterate, 1, '+')), loopj.iterate), loopk.iterate)
    rhs1 = Index(Index(Index(B, loopi.iterate), loopj.iterate), loopk.iterate)
	
    # body = Assignment(lhs, Expr(rhs1, rhs2, '+'))
    loopk.body.extend([Assignment(lhs1, Expr(rhs1, 2, '+'))])

    ir.extend([Decl(L)])
    ir.extend([Decl(M)])
    ir.extend([Decl(N)])
    ir.extend([Decl(A)])
    ir.extend([Decl(B)])
    ir.extend([loopi])

    return ir

def GetKeyInfo(loop_ir):
    def _GetKeyInfo(loop_ir, lower_bounds, upper_bounds, index_dict, level):
        if not type(loop_ir)==Loop:
            return
        if type(loop_ir)==Loop:
            lower_bounds.append(loop_ir.start)
            upper_bounds.append(loop_ir.end)
            index_dict[loop_ir.iterate] = level
            _GetKeyInfo(loop_ir.body[0], lower_bounds, upper_bounds, index_dict, level+1)

    index_dict = {}
    lower_bounds = []
    upper_bounds = []
    _GetKeyInfo(loop_ir, lower_bounds, upper_bounds, index_dict, 0)
    return lower_bounds, upper_bounds, index_dict

def GetNewUpperBound(upper_bound_expr, index_dict, tile_size_list):
    if type(upper_bound_expr)==Expr: # upper_bound_expr.left + upper_bound_expr.right 
        iterator_index = upper_bound_expr.left
        return Expr(upper_bound_expr, tile_size_list[index_dict[iterator_index]], '+')
    else:
        return upper_bound_expr
    
def GetNewLowerBound(lower_bound_expr, tile_size,i):
    # New lower bound(i) = Original lower bound(i) - (tile_size(i) - 1)
    return Expr(lower_bound_expr, Expr(tile_size[i], 1, '-'), '-')

def LoopTiling(ir, tile_size = []):
    new_ir = []
    low_bounds = []
    up_bounds = []
    bound_trim = " - " + str(tile_size) + " - 1"
    # print(bound_trim)
    for ir_item in ir:
        if type(ir_item) == Loop:
            lower_bounds, upper_bounds, index_dict = GetKeyInfo(ir_item)
            i = 0
            for lower_bound_expr in lower_bounds:
                #Type(upper_bound_expr) is an Exper or a nunmber
                new_lower_bound = GetNewLowerBound(lower_bound_expr, tile_size,i)
                i = i + 1
                low_bounds.append(new_lower_bound)
            PrintCCode(low_bounds)

            for upper_bound_expr in upper_bounds:
                #Type(upper_bound_expr) is an Exper or a nunmber
                new_upper_bound = GetNewUpperBound(upper_bound_expr, index_dict, tile_size)
                up_bounds.append(new_upper_bound)
            PrintCCode(up_bounds)
                
    return new_ir
            
	
if __name__ == "__main__":
    loop0_ir = Loop0()  # Loop0 is just an example
    PrintCCode(loop0_ir)

    loop0_ir_after_tiling = LoopTiling(loop0_ir, tile_size = [3,4,5])
    PrintCCode(loop0_ir_after_tiling)