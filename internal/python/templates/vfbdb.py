# This file has been automatically generated by the vfbdb tool.
# Do not edit it manually, unless you really know what you do.
# https://github.com/Functional-Bus-Description-Language/go-vfbdb

import math
import time

BUS_WIDTH = {{.BusWidth}}

def calc_mask(m):
    return (((1 << (m[0] + 1)) - 1) ^ ((1 << m[1]) - 1)) >> m[1]

class _BufferIface:
    """
    _BufferIface is the internal interface used for reading/writing internal buffer
    (after reading)/(before writing) the target buffer. It is very useful
    as it allows treating proc or stream params/returns as configs/statuses.
    """
    def set_buf(self, buf):
        self.buf = buf

    def write(self, addr, data):
        self.buf[addr] = data

    def read(self, addr):
        return self.buf[addr]

def pack_params(params, *args):
    buf = []
    addr = None # Current buffer address
    data = 0

    for i, arg in enumerate(args):
        param = params[i]
        assert 0 <= arg < 2 ** param['Width'], "data value overrange ({})".format(arg)

        a = param['Access']

        if addr is None:
            addr = a['StartAddr']
        elif a['StartAddr'] > addr:
            buf.append(data)
            data = 0
            addr = a['StartAddr']

        if a['Type'] == 'SingleSingle':
            data |= arg << a['StartBit']
        elif a['Type'] == 'SingleContinuous':
            for r in range(a['RegCount']):
                if r == 0:
                    data |= (arg & calc_mask((BUS_WIDTH - 1, a['StartBit']))) << a['StartBit']
                    buf.append(data)
                    arg = arg >> (BUS_WIDTH - a['StartBit'])
                else:
                    addr += 1
                    data = arg & calc_mask((BUS_WIDTH, 0))
                    arg = arg >> BUS_WIDTH
                    if r < a['RegCount'] - 1:
                        buf.append(data)
        else:
            for v in arg:
                assert 0 <= v < 2 ** param['Width'], "data value overrange ({})".format(v)

    buf.append(data)

    return buf

def crate_mock_returns(buf_iface, start_addr, returns):
    """
    Crate_mock_returns crates mock returns that can be used with internal software buffer.
    It is useful to be used with proc with returns and with upstram.
    """
    buf_size = 0
    rets = []
    for ret in returns:
        a = ret['Access']
        buf_size += a['RegCount']
        r = {}
        r['Name'] = ret['Name']
        # TODO: Add support for groups.

        if a['Type'] == 'SingleSingle':
            r['Status'] = StatusSingleSingle(
                buf_iface, a['StartAddr'] - start_addr, (a['EndBit'], a['StartBit'])
            )
        elif a['Type'] == 'SingleContinuous':
            r['Status'] = StatusSingleContinuous(
                buf_iface, a['StartAddr'] - start_addr, a['RegCount'], a['StartMask'], a['EndMask'], False,
            )
        else:
            raise Exception("not yet implemented")

        rets.append(r)

    return buf_size, rets

class EmptyProc():
    def __init__(self, iface, call_addr, delay, exit_addr):
        self.iface = iface
        self.call_addr = call_addr
        self.delay = delay
        self.exit_addr = exit_addr
    def __call__(self):
        self.iface.write(self.call_addr, 0)
        if self.delay is not None:
            if self.delay != 0:
                time.sleep(self.delay)
            self.iface.read(self.exit_addr)

class ParamsProc():
    def __init__(self, iface, params_start_addr, params, delay, exit_addr):
        self.iface = iface
        self.params_start_addr = params_start_addr
        self.params = params
        self.delay = delay
        self.exit_addr = exit_addr

    def __call__(self, *args):
        assert len(args) == len(self.params), \
            "{}() takes {} arguments but {} were given".format(self.__name__, len(self.params), len(args))

        buf = pack_params(self.params, *args)

        if len(buf) == 1:
            self.iface.write(self.params_start_addr, buf[0])
        else:
            self.iface.writeb(self.params_start_addr, buf)

        if self.delay is not None:
            if self.delay != 0:
                time.sleep(self.delay)
            self.iface.read(self.exit_addr)

class ReturnsProc():
    def __init__(self, iface, returns_start_addr, returns, delay, call_addr):
        self.iface = iface
        self.returns_start_addr = params_start_addr
        self.delay = delay
        self.exit_addr = exit_addr

        self.buf_iface = _BufferIface()
        self.buf_size, self.returns = crate_mock_returns(self.buf_iface, addr, returns)

    def __call__(self, *args):
        if self.delay is not None:
            self.iface.write(self.call_addr, 0)
            if self.delay != 0:
                time.sleep(self.delay)

        if self.buf_size == 1:
            buf = [self.iface.read(self.returns_start_addr)]
        else:
            buf = self.iface.readb(self.returns_start_addr, self.buf_size)

        self.buf_iface.set_buf(buf)
        tup = [] # List to allow append but must be cast to tuple.

        for ret in self.returns:
            # NOTE: Groups are not yet supported so it is safe to immediately append.
            tup.append(ret['Status'].read())

        return tuple(tup)


class SingleSingle:
    def __init__(self, iface, addr, mask):
        self.iface = iface
        self.addr = addr
        self.mask = calc_mask(mask)
        self.width = mask[0] - mask[1] + 1
        self.shift = mask[1]

    def read(self):
        return (self.iface.read(self.addr) >> self.shift) & self.mask

class SingleContinuous:
    def __init__(self, iface, start_addr, reg_count, start_mask, end_mask):
        self.iface = iface
        self.addrs = list(range(start_addr, start_addr + reg_count))
        self.width = 0
        self.masks = []
        self.reg_shifts = []
        self.data_shifts = []

        for i in range(reg_count):
            if i == 0:
                self.masks.append(calc_mask(start_mask))
                self.reg_shifts.append(start_mask[1])
                self.data_shifts.append(0)
                self.width += start_mask[0] - start_mask[1] + 1
            else:
                self.reg_shifts.append(0)
                self.data_shifts.append(self.width)
                if i == reg_count - 1:
                    self.masks.append(calc_mask(end_mask))
                    self.width += end_mask[0] - end_mask[1] + 1
                else:
                    self.masks.append(calc_mask((BUS_WIDTH - 1, 0)))
                    self.width += BUS_WIDTH

    def read(self):
        data = 0
        for i, a in enumerate(self.addrs):
            data |= ((self.iface.read(a) >> self.reg_shifts[i]) & self.masks[i]) << self.data_shifts[i]
        return data

class ConfigSingleSingle(SingleSingle):
    def __init__(self, iface, addr, mask):
        super().__init__(iface, addr, mask)

    def write(self, data):
        assert 0 <= data < 2 ** self.width, "value overrange ({})".format(data)
        self.iface.write(self.addr, data << self.shift)

class ConfigSingleContinuous(SingleContinuous):
    def __init__(self, iface, start_addr, reg_count, start_mask, end_mask):
        super().__init__(iface, start_addr, reg_count, start_mask, end_mask)

    def write(self, data):
        assert 0 <= data < 2 ** self.width, "value overrange ({})".format(data)
        for i, a in enumerate(self.addrs):
            self.iface.write(a, ((data >> self.data_shifts[i]) & self.masks[i]) << self.reg_shifts[i])

class MaskSingleSingle(SingleSingle):
    def __init__(self, iface, addr, mask):
        super().__init__(iface, addr, mask)

    def set(self, bits=None):
        if bits == None:
            bits = range(self.width)
        elif type(bits) == int:
            bits = [bits]

        mask = 0
        for b in bits:
            assert 0 <= b < self.width, "mask overrange"
            mask |= 1 << b

        self.iface.write(self.addr, mask << self.shift)

    def update(self, bits, mode="set"):
        if mode not in ["set", "clear"]:
            raise Exception("invalid mode '" + mode + "'")
        if bits == None:
            raise Exception("bits to update cannot have None value")
        if type(bits).__name__ in ["list", "tuple", "range", "set"] and len(bits) == 0:
            raise Exception("empty " + type(bits) + " of bits to update")

        mask = 0
        reg_mask = 0
        for b in bits:
            assert 0 <= b < self.width, "mask overrange"
            if mode == "set":
                mask |= 1 << b
            reg_mask |= 1 << b

        self.iface.rmw(self.addr, mask << self.shift, reg_mask << self.shift)

class Static:
    def __init__(self, value):
        self._value = value
    @property
    def value(self):
        return self._value
    @value.setter
    def value(self, v):
        raise Exception(f"cannot set value of static element")

class StaticSingleSingle(Static, SingleSingle):
    def __init__(self, iface, addr, mask, value):
        Static.__init__(self, value)
        SingleSingle.__init__(self, iface, addr, mask)

class StaticSingleContinuous(Static, SingleContinuous):
    def __init__(self, iface, start_addr, reg_count, start_mask, end_mask, value):
        Static.__init__(self, value)
        SingleContinuous.__init__(self, iface, start_addr, reg_count, start_mask, end_mask)

class StatusSingleSingle(SingleSingle):
    def __init__(self, iface, addr, mask):
        super().__init__(iface, addr, mask)

class StatusSingleContinuous(SingleContinuous):
    def __init__(self, iface, start_addr, reg_count, start_mask, end_mask):
        super().__init__(iface, start_addr, reg_count, start_mask, end_mask)

class StatusArraySingle:
    def __init__(self, iface, addr, mask, item_count):
        self.iface = iface
        self.addr = addr
        self.mask = calc_mask(mask)
        self.shift = mask[1]
        self.item_count = item_count

    def read(self, idx=None):
        if idx is None:
            idx = tuple(range(0, self.item_count))
        elif type(idx) == int:
            assert 0 <= idx < self.item_count
            return (self.iface.read(self.addr + idx) >> self.shift) & self.mask
        else:
            for i in idx:
                assert 0 <= i < self.item_count

        return [(self.iface.read(self.addr + i) >> self.shift) & self.mask for i in idx]


class StatusArrayMultiple:
    def __init__(self, iface, addr, start_bit, width, item_count, items_per_access):
        self.iface = iface
        self.addr = addr
        self.start_bit = start_bit
        self.width = width
        self.item_count = item_count
        self.items_per_access = items_per_access
        self.reg_count = math.ceil(item_count / self.items_per_access)

    def read(self, idx=None):
        if idx is None:
            idx = tuple(range(0, self.item_count))
            reg_idx = tuple(range(self.reg_count))
        elif type(idx) == int:
            assert 0 <= idx < self.item_count
            reg_idx = idx // self.items_per_access
            shift = self.start_bit + self.width * (idx % self.items_per_access)
            mask = (1 << self.width) - 1
            return (self.iface.read(self.addr + reg_idx) >> shift) & mask
        else:
            reg_idx = set()
            for i in idx:
                assert 0 <= i < self.item_count
                reg_idx.add(i // self.items_per_access)

        reg_data = {reg_i : self.iface.read(self.addr + reg_i) for reg_i in reg_idx}

        data = []
        for i in idx:
            shift = self.start_bit + self.width * (i % self.items_per_access)
            mask = (1 << self.width) - 1
            data.append((reg_data[i // self.items_per_access] >> shift) & mask)

        return data


class Upstream():
    def __init__(self, iface, addr, returns):
        self.iface = iface
        self.addr = addr
        self.buf_iface = _BufferIface()
        self.buf_size, self.returns = crate_mock_returns(self.buf_iface, addr, returns)

    def read(self, n):
        """
        Read the stream n times.
        Read returns a tuple of tuples. Grouped returns are returned as dictionary (not yet supported).
        Non grouped returns are returned as values within tuple.
        """
        if self.buf_size == 1:
            read_data = [[x] for x in self.iface.cread(self.addr, n)]
        else:
            read_data = self.iface.creadb(self.addr, self.buf_size, n)

        data = []
        for buf in read_data:
            self.buf_iface.set_buf(buf)
            tup = [] # List to allow append but must be cast to tuple.

            for ret in self.returns:
                # NOTE: Groups are not yet supported so it is safe to immediately append.
                tup.append(ret['Status'].read())

            data.append(tuple(tup))

        return tuple(data)

{{.Code}}
