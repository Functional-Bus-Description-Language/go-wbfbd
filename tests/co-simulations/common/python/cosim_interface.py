import os


class CosimInterface:
    def __init__(
        self, write_fifo_path, read_fifo_path, delay_function=None, delay=False
    ):
        """Create co-simulation interface.
        Parameters:
        -----------
        write_fifo_path
            Path to software -> firmware named pipe.
        read_fifo_path
            Path to firmware -> software named pipe.
        delay_function
            Reference to function returning random value when delay is set to 'True'.
        delay
            If set to 'True' there is a random delay between any write or read operation.
            Useful for modelling real access times.
        """
        self.write_fifo_path = write_fifo_path
        self.read_fifo_path = read_fifo_path

        self._make_fifos()
        self.write_fifo = open(write_fifo_path, "w")
        self.read_fifo = open(read_fifo_path, "r")

        if delay and delay_function is None:
            raise Exception("delay set to 'True', but delay_function not provided")

        self.delay_function = delay_function
        self.delay = delay

        # Attributes related with statistics collection.
        self.write_count = 0
        self.read_count = 0
        self.rmw_count = 0

    def _make_fifos(self):
        """Create named pipes needed for inter-process communication."""
        self._remove_fifos()
        print("CosimInterface: making FIFOs")
        os.mkfifo(self.write_fifo_path)
        os.mkfifo(self.read_fifo_path)

    def _remove_fifos(self):
        """Remove named pipes."""
        try:
            print("CosimInterface: removing FIFOs")
            os.remove(self.write_fifo_path)
            os.remove(self.read_fifo_path)
        except:
            pass

    def write(self, addr, val):
        """Write register.
        Parameters
        ----------
        addr
            Register address.
        val
            Value to be written.
        """
        if self.delay:
            self.wait(self.delay_function())

        print(
            "write: address 0x{:08x}, value {} (0x{:08x}) (0b{:032b})".format(addr, val, val, val)
        )

        cmd = "W" + ("%.8x" % addr) + "," + ("%.8x" % val) + "\n"
        self.write_fifo.write(cmd)
        self.write_fifo.flush()

        s = self.read_fifo.readline()
        if s.strip() == "ACK":
            self.write_count += 1
            return
        else:
            raise Exception("Wrong status returned:" + s.strip())

    def read(self, addr):
        """Read register.

        Parameters
        ----------
        addr
            Register address.
        """
        if self.delay:
            self.wait(self.delay_function())

        print("read: address 0x{:08x}".format(addr))

        cmd = "R" + ("%.8x" % addr) + "\n"
        self.write_fifo.write(cmd)
        self.write_fifo.flush()

        s = self.read_fifo.readline()
        if s.strip() == "ERR":
            raise Exception("Error status returned")

        self.read_count += 1
        val = int(s, 2)
        print("read: value {} (0x{:08x}) (0b{:032b})".format(val, val, val))

        return val

    def rmw(self, addr, val, mask):
        """Perform read-modify-write operation.
        New value is determined by following formula: X := (X & ~mask) | (val & mask).

        Parameters:
        addr
            Register address.
        val
            Value.
        mask
            Mask.
        """
        print(
            "rmw: address 0x%.8x, value %d (0x%.8x) (%s), mask %d (%s)"
            % (addr, val, val, bin(val), mask, bin(mask))
        )
        X = self.read(addr)
        self.write(addr, (X & abs(mask - 0xFFFFFFFF)) | (val & mask))

        self.rmw_count += 1

    def wait(self, time_ns):
        """Wait in the simulator for a given amount of time.
        Parameters
        ----------
        time_ns
            Time to wait in nanoseconds.
        """
        assert time_ns > 0, "Wait time must be greater than 0"

        print("wait for %d ns" % time_ns)

        cmd = "T" + ("%.8x" % time_ns) + "\n"
        self.write_fifo.write(cmd)
        self.write_fifo.flush()

        s = self.read_fifo.readline()
        if s.strip() == "ACK":
            return
        else:
            raise Exception("Wrong status returned:" + s.strip())

    def end(self, status):
        """End a co-simulation with a given status.
        Parameters:
        -----------
        status
            Status to be returned by the simulation process.
        """
        print("CosimInterface: ending with status %d" % status)

        cmd = "E" + ("%.8x" % status) + "\n"
        self.write_fifo.write(cmd)
        self.write_fifo.flush()

        s = self.read_fifo.readline()
        if s.strip() == "ACK":
            self._remove_fifos()
        else:
            raise Exception("Wrong status returned:" + s.strip())
        self.print_stats()

    def print_stats(self):
        print(
            f"\nCosimInterface: transactions statistics:\n"
            + f"  Write Count: {self.write_count}\n"
            + f"  Read Count:  {self.read_count}\n"
            + f"  RMW Count:   {self.rmw_count}"
        )
