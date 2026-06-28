library ieee;
use ieee.std_logic_1164.all;

entity sqrt_top is
    port (
        clk, rst, start : in  std_logic;
        sel             : in  std_logic;
        data_in         : in  std_logic_vector(31 downto 0);
        data_out        : out std_logic_vector(31 downto 0);
        done            : out std_logic
    );
end entity;

architecture rtl of sqrt_top is
    signal d_std, d_lossy : std_logic_vector(31 downto 0);
    signal v_std, v_lossy : std_logic;
begin
    -- Instantiate all three
    U_STD: entity work.sqrt_standard port map(clk, rst, start, data_in, d_std, v_std);
    U_LSY: entity work.sqrt_lossy    port map(clk, rst, start, data_in, d_lossy, v_lossy);

    -- Mux logic
    process(sel, d_std, d_lossy, v_std, v_lossy)
    begin
        case sel is
            when '0' => data_out <= d_std;    done <= v_std;
            when '1' => data_out <= d_lossy;  done <= v_lossy;
            when others => data_out <= (others => '0');
        end case;
    end process;
end rtl;