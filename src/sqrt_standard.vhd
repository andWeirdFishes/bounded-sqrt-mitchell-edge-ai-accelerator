library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity sqrt_standard is
    port (
        clk, rst, start : in std_logic;
        data_in         : in std_logic_vector(31 downto 0);
        data_out        : out std_logic_vector(31 downto 0);
        done            : out std_logic
    );
end;

architecture rtl of sqrt_standard is
    signal x     : unsigned(31 downto 0);
    signal root  : unsigned(23 downto 0);
    signal rema  : unsigned(25 downto 0);
    signal count : integer range 0 to 24;
    signal busy  : std_logic;
    signal phase : std_logic;
begin
    process(clk, rst)
        variable trial_v : unsigned(25 downto 0);
        variable rema_v  : unsigned(25 downto 0);
        variable root_v  : unsigned(23 downto 0);
    begin
        if rst = '1' then
            busy  <= '0';
            done  <= '0';
            phase <= '0';
        elsif rising_edge(clk) then
            if start = '1' and busy = '0' then
                x     <= unsigned(data_in);
                root  <= (others => '0');
                rema  <= (others => '0');
                count <= 24;
                busy  <= '1';
                done  <= '0';
                phase <= '0';
            elsif busy = '1' then
                trial_v := resize(root & "01", 26);

                if phase = '0' then
                    rema_v := rema(23 downto 0) & x(31 downto 30);
                    x      <= x(29 downto 0) & "00";
                    if count = 9 then
                        phase <= '1';
                    end if;
                else
                    rema_v := rema(23 downto 0) & "00";
                end if;

                if rema_v >= trial_v then
                    rema   <= rema_v - trial_v;
                    root_v := root(22 downto 0) & '1';
                else
                    rema   <= rema_v;
                    root_v := root(22 downto 0) & '0';
                end if;
                root <= root_v;

                if count = 1 then
                    busy     <= '0';
                    done     <= '1';
                    data_out <= std_logic_vector(resize(root_v, 32));
                    count    <= 0;
                else
                    done  <= '0';
                    count <= count - 1;
                end if;
            else
                done <= '0';
            end if;
        end if;
    end process;
end rtl;