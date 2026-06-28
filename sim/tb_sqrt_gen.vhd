library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.textio.all;
use std.env.all;

entity tb_sqrt_gen is
    generic (
        sel_gen : std_logic := '0'
    );
end entity;

architecture sim of tb_sqrt_gen is
    signal clk : std_logic := '0';
    signal rst : std_logic := '1';
    signal start : std_logic := '0';
    signal data_in, data_out : std_logic_vector(31 downto 0);
    signal done : std_logic;

    file infile : text open read_mode is "sim/input_data.txt";
    file outfile : text;
begin
    clk <= not clk after 5 ns;

    uut: entity work.sqrt_top 
        port map(
            clk      => clk, 
            rst      => rst, 
            start    => start, 
            sel      => sel_gen,
            data_in  => data_in, 
            data_out => data_out, 
            done     => done
        );

    process
        variable l, o : line;
        variable val : std_logic_vector(31 downto 0);
    begin
        case sel_gen is
            when '0' => file_open(outfile, "sim/output_standard.txt", write_mode);
            when '1' => file_open(outfile, "sim/output_lossy.txt", write_mode);
            when others => file_open(outfile, "sim/output_unknown.txt", write_mode);
        end case;
        wait for 20 ns;
        rst <= '0';
        wait until rising_edge(clk);

        while not endfile(infile) loop
            readline(infile, l);
            if l'length > 0 then
                hread(l, val);
                data_in <= val;

                wait until rising_edge(clk);
                start <= '1';
                wait until rising_edge(clk);
                start <= '0';

                wait until done = '1' for 500 ns;

                if done = '1' then
                    write(o, to_integer(unsigned(data_out)));
                    writeline(outfile, o);
                else
                    report "FAIL: Timeout on input " & to_hstring(val) severity failure;
                end if;

                wait until rising_edge(clk);
            end if;
        end loop;

        report "SUCCESS: All samples processed.";
        finish;
    end process;
end sim;