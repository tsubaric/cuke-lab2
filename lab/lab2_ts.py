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

def SetKeyInfo(loop_ir, low_bounds, up_bounds, tile_size):
    def _SetKeyInfo(loop_ir, low_bounds, up_bounds, level, tile_size):
        if not type(loop_ir)==Loop:
            return
        if type(loop_ir)==Loop:
            loop_ir.start = low_bounds[level]
            loop_ir.end = up_bounds[level]
            loop_ir.step = tile_size[level]
            _SetKeyInfo(loop_ir.body[0], low_bounds, up_bounds, level+1, tile_size)
    
    _SetKeyInfo(loop_ir, low_bounds, up_bounds, 0, tile_size)
    return loop_ir

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
    if type(upper_bound_expr)==Expr: 
        iterator_index = upper_bound_expr.left
        return Expr(upper_bound_expr, tile_size_list[index_dict[iterator_index]], '+')
    else:
        return upper_bound_expr
    
def GetNewLowerBound(lower_bound_expr, tile_size, i):
    return Expr(lower_bound_expr, Expr(tile_size[i], 1, '-'), '-')

def FindBody(nested_loop):
    if not type(nested_loop) == Loop:
        return nested_loop
    if type(nested_loop.body[0]) == Loop:
        return FindBody(nested_loop.body[0])
    else:
        return nested_loop.body
    
def point_loops(org_low, org_up, index_dict, tile_size, num_of_loops,bodyyy):
    point_ir = []
    loops = [0 for _ in range(num_of_loops)]
    tile_loop_iter = list(index_dict.keys())
    
    for kk in range(0,num_of_loops):
        loops[kk] = Loop(Max(tile_loop_iter[kk],org_low[kk]), Min(Expr(tile_loop_iter[kk],tile_size[kk],'+'),org_up[kk]),1,[])
      
    for jj in range(num_of_loops-1):
        loops[jj].body.append(loops[jj+1])  
    
    loops[-1].body.extend(bodyyy)
    point_ir.extend([loops[0]])
    
    return point_ir

def merge(tiled_loops, point_loops):
    if not type(tiled_loops) == Loop:
        tiled_loops = point_loops
    if type(tiled_loops.body[0]) == Loop:
        return merge(tiled_loops.body[0], point_loops)
    else:
        tiled_loops.body = point_loops


def LoopTiling(ir, tile_size = []):
    new_ir = []
    low_bounds = []
    up_bounds = []
    body = ""

    for ir_item in ir:
        if type(ir_item) == Loop:
            org_lower, org_upper, index_dict = GetKeyInfo(ir_item)
            i = 0
            for lower_bound_expr in org_lower:
                new_lower_bound = GetNewLowerBound(lower_bound_expr, tile_size, i)
                low_bounds.append(new_lower_bound)
                i = i + 1

            for upper_bound_expr in org_upper:
                new_upper_bound = GetNewUpperBound(upper_bound_expr, index_dict, tile_size)
                up_bounds.append(new_upper_bound)

            ir_item = SetKeyInfo(ir_item, low_bounds, up_bounds, tile_size)
            body = FindBody(ir_item)

    point_loops_ir = point_loops(org_lower, org_upper, index_dict, tile_size, len(low_bounds), body)

    for ir_item in ir:
         if type(ir_item) == Loop:
              merge(ir_item, point_loops_ir)

    print("============================> New Lower Bounds")
    PrintCCode(low_bounds)
    
    print("============================> New Upper Bounds")
    PrintCCode(up_bounds)
    
    print("============================> New Points Loops Generated")
    PrintCCode(point_loops_ir)  
    
    print("============================> Inner Most Statements")
    PrintCCode(body)
    
    print("============================> Merged Final Loops")
    PrintCCode(ir)
                
    return new_ir
            
if __name__ == "__main__":
    loop0_ir = Loop0()  # Loop0 is just an example
    # PrintCCode(loop0_ir)

    loop0_ir_after_tiling = LoopTiling(loop0_ir, tile_size = [3,4,5])
    # PrintCCode(loop0_ir_after_tiling)