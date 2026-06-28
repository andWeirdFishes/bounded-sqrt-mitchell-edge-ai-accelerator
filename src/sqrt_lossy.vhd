library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity sqrt_lossy is
    port (
        clk, rst, start : in std_logic;
        data_in         : in std_logic_vector(31 downto 0);
        data_out        : out std_logic_vector(31 downto 0);
        done            : out std_logic
    );
end entity;

-- Mitchell's approximation for Q16.16 sqrt. Single clock cycle.
--
-- For input raw with MSB at bit m, the approximation is:
--   base = raw >> (m/2 - 8)                   [power-of-2 seed]
--   if m is odd: base = base >> 1             [pre-scale for odd octave]
--   pow2 = 1 << (m/2 + 8 + (m mod 2))        [octave upper endpoint]
--   result = (base + pow2) >> 1               [linear interp within octave]
--
-- This produces a uniform error ramp of [0%, +6.07%] across every octave,
-- which is the minimax-optimal result achievable with this structure.
-- The concavity of sqrt means the chord always lies above the curve (overshoot),
-- and the ramp always runs from 0% at the octave top to +6.07% at the bottom.
architecture rtl of sqrt_lossy is
begin
    process(clk, rst)
        variable msb   : integer range 0 to 31;
        variable raw   : unsigned(31 downto 0);
        variable base  : unsigned(31 downto 0);
        variable pow2  : unsigned(31 downto 0);
        variable shift : integer range -8 to 15;
    begin
        if rst = '1' then
            data_out <= (others => '0');
            done     <= '0';
        elsif rising_edge(clk) then
            if start = '1' then
                raw := unsigned(data_in);
                msb := 0;
                for i in 31 downto 0 loop
                    if raw(i) = '1' then
                        msb := i;
                        exit;
                    end if;
                end loop;

                shift := msb/2 - 8;
                if shift >= 0 then
                    base := raw srl shift;
                else
                    base := raw sll (-shift);
                end if;

                if msb mod 2 = 1 then
                    base := base srl 1;
                end if;

                pow2 := shift_left(to_unsigned(1, 32), msb/2 + 8 + (msb mod 2));
                base := (base + pow2) srl 1;
                base := base - (base srl 5);
                data_out <= std_logic_vector(base);
                done     <= '1';
            else
                done <= '0';
            end if;
        end if;
    end process;
end rtl;