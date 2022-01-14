-- This file has been automatically generated by the wbfbd tool.
-- Do not edit it manually, unless you really know what you do.
-- https://github.com/Functional-Bus-Description-Language/go-wbfbd

library ieee;
   use ieee.std_logic_1164.all;
   use ieee.numeric_std.all;

library work;
   use work.wbfbd.all;


package {{.EntityName}}_pkg is

-- Constants
{{.Constants}}
-- Func types
{{.FuncTypes}}
end package;


library ieee;
   use ieee.std_logic_1164.all;
   use ieee.numeric_std.all;

library general_cores;
   use general_cores.wishbone_pkg.all;

library work;
   use work.wbfbd.all;
   use work.{{.EntityName}}_pkg.all;


entity {{.EntityName}} is
generic (
   G_REGISTERED : boolean := true
);
port (
   clk_i : in std_logic;
   rst_i : in std_logic;
   slave_i : in  t_wishbone_slave_in_array ({{.MastersCount}} - 1 downto 0);
   slave_o : out t_wishbone_slave_out_array({{.MastersCount}} - 1 downto 0){{.EntitySubblockPorts}}{{.EntityFunctionalPorts}}
);
end entity;


architecture rtl of {{.EntityName}} is

constant C_ADDRESSES : t_wishbone_address_array({{.SubblocksCount}} downto 0) := ({{.AddressValues}});
constant C_MASKS     : t_wishbone_address_array({{.SubblocksCount}} downto 0) := ({{.MaskValues}});

signal master_out : t_wishbone_master_out;
signal master_in  : t_wishbone_master_in;

{{.SignalDeclarations}}
begin

crossbar: entity general_cores.xwb_crossbar
generic map (
   G_NUM_MASTERS => {{.MastersCount}},
   G_NUM_SLAVES  => {{.SubblocksCount}} + 1,
   G_REGISTERED  => G_REGISTERED,
   G_ADDRESS     => C_ADDRESSES,
   G_MASK        => C_MASKS
)
port map (
   clk_sys_i   => clk_i,
   rst_n_i     => not rst_i,
   slave_i     => slave_i,
   slave_o     => slave_o,
   master_i(0) => master_in,{{.CrossbarSubblockPortsIn}}
   master_o(0) => master_out{{.CrossbarSubblockPortsOut}}
);


register_access : process (all) is

variable addr : natural range 0 to {{.RegistersCount}} - 1;

begin

if rising_edge(clk_i) then

-- Normal operation.
master_in.rty <= '0';
master_in.ack <= '0';
master_in.err <= '0';

-- Funcs Strobes Clear{{.FuncsStrobesClear}}

transfer : if
   master_out.cyc = '1'
   and master_out.stb = '1'
   and master_in.err = '0'
   and master_in.rty = '0'
   and master_in.ack = '0'
then
   addr := to_integer(unsigned(master_out.adr({{.InternalAddrBitsCount}} - 1 downto 0)));

   -- First assume there is some kind of error.
   -- For example internal address is invalid or there is a try to write status.
   master_in.err <= '1';
   -- '0' for security reasons, '-' can lead to the information leak.
   master_in.dat <= (others => '0');
   master_in.ack <= '0';

   -- Registers Access{{range $addr, $code := .RegistersAccess}}
   if {{index $addr 0}} <= addr and addr <= {{index $addr 1}} then
{{$code}}

      master_in.ack <= '1';
      master_in.err <= '0';
   end if;
{{end}}

   -- Funcs Strobes Set{{.FuncsStrobesSet}}

end if transfer;

if rst_i = '1' then
   master_in <= C_DUMMY_WB_MASTER_IN;
end if;
end if;
end process;

end architecture;
