#%%
from pygmyhdl import *

@chunk
def pwm_simple(clk_i, pwm_o, threshold):
    '''
    Inputs:
        clk_i: PWM changes state on the rising edge of this clock input.
        threshold: Bit-length determines counter width and value determines when output goes low.
    Outputs:
        pwm_o: PWM output starts and stays high until counter > threshold and then output goes low.
    '''
    cnt = Bus(len(threshold), name='cnt')  # Create a counter with the same number of bits as the threshold.

    # Here's the sequential logic for incrementing the counter. We've seen this before!
    @seq_logic(clk_i.posedge)
    def cntr_logic():
        cnt.next = cnt + 1

    # Combinational logic that drives the PWM output high when the counter is less than the threshold.
    @comb_logic
    def output_logic():
        pwm_o.next = cnt < threshold  # cnt<threshold evaluates to either True (1) or False (0).


#%%
@chunk
def pwm_less_simple(clk_i, pwm_o, threshold, duration):
    '''
    Inputs:
        clk_i: PWM changes state on the rising edge of this clock input.
        threshold: Determines when output goes low.
        duration: The length of the total pulse duration as determined by the counter.
    Outputs:
        pwm_o: PWM output starts and stays high until counter > threshold and then output goes low.
    '''
    # The log2 of the pulse duration determines the number of bits needed
    # in the counter. The log2 value is rounded up to the next integer value.
    import math
    length = math.ceil(math.log(duration, 2))
    cnt = Bus(length, name='cnt')

    # Augment the counter with a comparator to adjust the pulse duration.
    @seq_logic(clk_i.posedge)
    def cntr_logic():
        cnt.next = cnt + 1
        # Reset the counter to zero once it reaches one less than the desired duration.
        # So if the duration is 3, the counter will count 0, 1, 2, 0, 1, 2...
        if cnt == duration-1:
            cnt.next = 0

    @comb_logic
    def output_logic():
        pwm_o.next = cnt < threshold
# %%
@chunk
def pwm_glitchless(clk_i, pwm_o, threshold, interval):
    import math
    length = math.ceil(math.log(interval, 2))
    cnt = Bus(length)

    threshold_r = Bus(length, name='threshold_r') # Create a register to hold the threshold value.

    @seq_logic(clk_i.posedge)
    def cntr_logic():
        cnt.next = cnt + 1
        if cnt == interval-1:
            cnt.next = 0
            threshold_r.next = threshold  # The threshold only changes at the end of a pulse.

    @comb_logic
    def output_logic():
        pwm_o.next = cnt < threshold_r
# %%
@chunk
def ramp(clk_i, ramp_o):
    '''
    Inputs:
        clk_i: Clock input.
    Outputs:
        ramp_o: Multi-bit amplitude of ramp.
    '''

    # Delta is the increment (+1) or decrement (-1) for the counter.
    delta = Bus(len(ramp_o))

    @seq_logic(clk_i.posedge)
    def logic():
        # Add delta to the current ramp value to get the next ramp value.
        ramp_o.next = ramp_o + delta

        # When the ramp reaches the bottom, set delta to +1 to start back up the ramp.
        if ramp_o == 1:
            delta.next = 1

        # When the ramp reaches the top, set delta to -1 to start back down the ramp.
        elif ramp_o == ramp_o.max-2:
            delta.next = -1

        # After configuring the FPGA, the delta register is set to zero.
        # Set it to +1 and set the ramp value to +1 to get things going.
        elif delta == 0:
            delta.next = 1
            ramp_o.next = 1
# %%
@chunk
def wax_wane(clk_i, led_o, length):
    rampout = Bus(length, name='ramp')  # Create the triangle ramp counter register.
    ramp(clk_i, rampout)  # Generate the ramp.
    pwm_simple(clk_i, led_o, rampout.o[length:length-4]) # Use the upper 4 ramp bits to drive the PWM threshold
# %%
initialize()
clk = Wire(name='clk')
led = Wire(name='led')
wax_wane(clk, led, 6)
# %%
toVerilog(wax_wane, clk, led, 23)
# %%
