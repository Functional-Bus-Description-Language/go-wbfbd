library work;
   context work.cosim_context;
   use work.cosim.all;


entity tb_cosim is
   generic(
      G_SW_FW_FIFO_PATH : string;
      G_FW_SW_FIFO_PATH : string
   );
end entity;


architecture test of tb_cosim is

   signal clk : std_logic := '0';

   signal status_array0 : t_slv_vector(7 downto 0)(7 downto 0) := (
      0 => "00000000",
      1 => "00000001",
      2 => "00000010",
      3 => "00000011",
      4 => "00000100",
      5 => "00000101",
      6 => "00000110",
      7 => "00000111"
   );

   signal status_array1 : t_slv_vector(3 downto 0)(4 downto 0) := (
      0 => "00000",
      1 => "00001",
      2 => "00010",
      3 => "00011"
   );

   -- Wishbone interfaces.
   signal uvvm_wb_if : t_wishbone_if (
      dat_o(31 downto 0),
      dat_i(31 downto 0),
      adr_o(31 downto 0)
   ) := init_wishbone_if_signals(32, 32);

   signal wb_ms: t_wishbone_master_out;
   signal wb_sm: t_wishbone_slave_out;

begin

   clk <= not clk after C_CLK_PERIOD / 2;


   wb_ms.cyc <= uvvm_wb_if.cyc_o;
   wb_ms.stb <= uvvm_wb_if.stb_o;
   wb_ms.adr <= uvvm_wb_if.adr_o;
   wb_ms.sel <= (others => '0');
   wb_ms.we  <= uvvm_wb_if.we_o;
   wb_ms.dat <= uvvm_wb_if.dat_o;

   uvvm_wb_if.dat_i <= wb_sm.dat;
   uvvm_wb_if.ack_i <= wb_sm.ack;

   cosim_interface(G_SW_FW_FIFO_PATH, G_FW_SW_FIFO_PATH, clk, uvvm_wb_if, C_WB_BFM_CONFIG);


   wbfbd_main : entity wbfbd.main
   port map (
      clk_i => clk,
      rst_i => '0',
      slave_i(0) => wb_ms,
      slave_o(0) => wb_sm,
      status_array0_i => status_array0,
      status_array1_i => status_array1
   );

end architecture;
