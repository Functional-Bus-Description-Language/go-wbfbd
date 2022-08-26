package csync

import (
	"fmt"

	"github.com/Functional-Bus-Description-Language/go-fbdl/pkg/fbdl/access"
	"github.com/Functional-Bus-Description-Language/go-fbdl/pkg/fbdl/elem"
	"github.com/Functional-Bus-Description-Language/go-vfbdb/internal/c"
	"github.com/Functional-Bus-Description-Language/go-vfbdb/internal/utils"
)

func genConfig(cfg elem.Config, hFmts *BlockHFormatters, cFmts *BlockCFormatters) {
	if cfg.IsArray() {
		panic("not yet implemented")
	} else {
		genConfigSingle(cfg, hFmts, cFmts)
	}
}

func genConfigSingle(cfg elem.Config, hFmts *BlockHFormatters, cFmts *BlockCFormatters) {
	switch cfg.Access().(type) {
	case access.SingleSingle:
		genConfigSingleSingle(cfg, hFmts, cFmts)
	case access.SingleContinuous:
		panic("not yet implemented")
	default:
		panic("unknown single access strategy")
	}
}

func genConfigSingleSingle(cfg elem.Config, hFmts *BlockHFormatters, cFmts *BlockCFormatters) {
	rType := c.WidthToReadType(cfg.Width())
	wType := c.WidthToWriteType(cfg.Width())

	readSignature := fmt.Sprintf(
		"int vfbdb_%s_%s_read(const vfbdb_iface_t * const iface, %s const data)",
		hFmts.BlockName, cfg.Name(), rType.String(),
	)
	writeSignature := fmt.Sprintf(
		"int vfbdb_%s_%s_write(const vfbdb_iface_t * const iface, %s const data)",
		hFmts.BlockName, cfg.Name(), wType.String(),
	)

	hFmts.Code += fmt.Sprintf("\n\n%s;\n%s;", readSignature, writeSignature)

	a := cfg.Access().(access.SingleSingle)
	cFmts.Code += fmt.Sprintf("\n\n%s {\n", readSignature)
	if readType.Typ() != "ByteArray" && rType.Typ() != "ByteArray" {
		if busWidth == cfg.Width() {
			cFmts.Code += fmt.Sprintf(
				"\treturn iface->read(%d, data);\n};", a.Addr,
			)
		} else {
			cFmts.Code += fmt.Sprintf(`	%s aux;
	const int err = iface->read(%d, &aux);
	if (err)
		return err;
	*data = (aux >> %d) & 0x%x;
	return 0;
};`, readType.Depointer().String(), a.Addr, a.StartBit(), utils.Uint64Mask(a.StartBit(), a.EndBit()),
			)
		}
	} else {
		panic("not yet implemented")
	}

	cFmts.Code += fmt.Sprintf("\n\n%s {\n", writeSignature)
	if readType.Typ() != "ByteArray" && rType.Typ() != "ByteArray" {
		if busWidth == cfg.Width() {
			cFmts.Code += fmt.Sprintf(
				"\treturn iface->write(%d, data);\n};", a.Addr,
			)
		} else {
			cFmts.Code += fmt.Sprintf(
				"	return iface->write(%d, (data << %d));\n };", a.Addr, a.StartBit(),
			)
		}
	} else {
		panic("not yet implemented")
	}
}
