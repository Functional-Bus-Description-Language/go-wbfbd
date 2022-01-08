package python

import (
	"fmt"

	"github.com/Functional-Bus-Description-Language/go-fbdl/pkg/fbdl"
)

func generateConfig(cfg *fbdl.Config, blk *fbdl.Block) string {
	if cfg.IsArray {
		return generateConfigArray(cfg, blk)
	} else {
		return generateConfigSingle(cfg, blk)
	}
}

func generateConfigSingle(cfg *fbdl.Config, blk *fbdl.Block) string {
	var code string

	switch cfg.Access.(type) {
	case fbdl.AccessSingleSingle:
		a := cfg.Access.(fbdl.AccessSingleSingle)
		code += indent + fmt.Sprintf(
			"self.%s = ConfigSingleSingle(interface, %d, (%d, %d))\n",
			cfg.Name, blk.AddrSpace.Start()+a.Addr, a.Mask.Upper, a.Mask.Lower,
		)
	case fbdl.AccessSingleContinuous:
		a := cfg.Access.(fbdl.AccessSingleContinuous)
		increasigOrder := "True"
		if a.IncreasingOrder() == false {
			increasigOrder = "False"
		}
		code += indent + fmt.Sprintf(
			"self.%s = ConfigSingleContinuous(interface, %d, %d, (%d, %d), (%d, %d), %s)\n",
			cfg.Name,
			blk.AddrSpace.Start()+a.StartAddr(),
			a.RegCount(),
			a.StartMask.Upper, a.StartMask.Lower,
			a.EndMask.Upper, a.EndMask.Lower,
			increasigOrder,
		)
	default:
		panic("not yet implemented")
	}

	return code
}

func generateConfigArray(cfg *fbdl.Config, blk *fbdl.Block) string {
	panic("not yet implemented")
}
