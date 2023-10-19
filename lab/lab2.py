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
    # if i is an expression of k:  
    #     New upper bound(i) = Original upper bound(i) + (tile_size(k) -1) 
    # else
    #     New upper bound(i) = Original upper bound(i)

    if type(upper_bound_expr)==Expr: # upper_bound_expr.left + upper_bound_expr.right 
        # upper_bound_expr.left  is k in the algorithm 
        iterator_index = upper_bound_expr.left
        return Expr(upper_bound_expr, tile_size_list[index_dict[iterator_index]], '+')
    else:
        return upper_bound_expr
    
def GetNewLowerBound(lower_bound_expr, tile_size):
    # New lower bound(i) = Original lower bound(i) - (tile_size(i) - 1)
    return Expr(lower_bound_expr, Expr(tile_size, 1, '-'), '-')

# def LoopTiling(ir, tile_size = []):
#     tiled_ir = []
#     for stmt in ir:
#         if isinstance(stmt, Loop):
#             new_loop = Loop(stmt.start, stmt.end, stmt.step, [])
#             new_loop.body = LoopTiling(stmt.body, tile_size)
#             tiled_ir.append(new_loop)
#         else:
#             tiled_ir.append(stmt)
#     return tiled_ir

def LoopTiling(ir, tile_size = []):
    for ir_item in ir:
        if type(ir_item) == Loop:
            # for (int _l0 = 0; _l0 < 20; _l0 += 1) {
            # for (int _l1 = _l0 + 3; _l1 < _l0 + 10; _l1 += 1) {
            # for (int _l2 = _l1 + 20; _l2 < _l1 + 30; _l2 += 1) {   
            #lower_bounds and upper_bounds are two lists recording the IRs of 
            #all corresponding lower bounds and upper bounds. 

            #index_dict is an dict recording the mapping between the index IR and loop index
            #Since _l0, _l1 and _l2 are the scalar objects instead of a number. 

            #lower_bounds is an array: [0, _l0 + 3, _l1 + 20]
            #upper_bounds is an array: [20, _l0 + 10, _l1 + 30]
            #index_dict is a map: { _l0: 0, 
            #                       _l1: 1,  
            #                       _l2: 2}
            lower_bounds, upper_bounds, index_dict = GetKeyInfo(ir_item)
            # PrintCCode(lower_bounds)
            # PrintCCode(upper_bounds)

            # for item in index_dict.items():
            #     PrintCCode([item[0]])
            #     PrintCCode([item[1]])

            for upper_bound_expr in upper_bounds:
                #Type(upper_bound_expr) is an Exper or a nunmber
                new_upper_bound = GetNewUpperBound(upper_bound_expr, index_dict, tile_size)
                PrintCCode([new_upper_bound])
	
if __name__ == "__main__":
    loop0_ir = Loop0()  # Loop0 is just an example
    # PrintCCode(loop0_ir)

    loop0_ir_after_tiling = LoopTiling(loop0_ir, tile_size = [3,4,5])
    # PrintCCode(loop0_ir_after_tiling)