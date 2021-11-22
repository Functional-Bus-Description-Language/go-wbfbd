package python

import (
	"fmt"
	"github.com/Functional-Bus-Description-Language/go-fbdl/pkg/fbdl"
)

func generateFunc(block *fbdl.Block, fun *fbdl.Func) string {
	var code string

	if fun.AreAllParamsSingleSingle() {
		code = generateFuncSingleSingle(block, fun)
	} else {
		panic("not yet implemented")
	}

	return code
}

func generateFuncFunctionSignature(fun *fbdl.Func) string {
	code := indent + fmt.Sprintf("def %s(self, ", fun.Name)
	for _, p := range fun.Params {
		code += p.Name + ", "
	}
	code = code[:len(code)-2]
	code += "):\n"

	increaseIndent(1)

	return code
}

// generateFuncSingleSingle generates function body for func which all parameters are of type AccessSingleSingle.
// In such case there is no Python for loop as it is relatiely easy to unroll during code generation.
func generateFuncSingleSingle(block *fbdl.Block, fun *fbdl.Func) string {
	code := generateFuncFunctionSignature(fun)

	val := ""
	for i, p := range fun.Params {
		access := p.Access.(fbdl.AccessSingleSingle)
		val += fmt.Sprintf("%s << %d | ", p.Name, access.Mask.Lower)
		if i == len(fun.Params)-1 || fun.Params[i+1].Access.StartAddr() != access.Addr {
			val = val[:len(val)-3]
			code += indent + fmt.Sprintf("self.interface.write(%d, %s)\n", block.AddrSpace.Start()+access.Addr, val)
			val = ""
		}
	}

	decreaseIndent(1)
	//code += indent + fmt.Sprintf("self.%s = func_%[1]s\n", fun.Name)

	return code
}