onerror {resume}
quietly WaveActivateNextPane {} 0
add wave -noupdate -color Magenta -radix ascii -radixshowbase 0 /risc_tb/wave_msg
add wave -noupdate -color {Cornflower Blue} -label {MC0 Instruction} -radix ascii -radixshowbase 0 /risc_tb/iw0
add wave -noupdate -color {Cornflower Blue} -label {MC1 Instruction} -radix ascii -radixshowbase 0 /risc_tb/iw1
add wave -noupdate -color {Cornflower Blue} -label {MC2 Instruction} -radix ascii -radixshowbase 0 /risc_tb/iw2
add wave -noupdate -color {Cornflower Blue} -label {MC3 Instruction} -radix ascii -radixshowbase 0 /risc_tb/iw3
add wave -noupdate -label Clock /risc_tb/dut/clk
TreeUpdate [SetDefaultTree]
quietly WaveActivateNextPane
add wave -noupdate -label nReset /risc_tb/dut/rst
add wave -noupdate -label {Input Peripherals} -radix hexadecimal /risc_tb/dut/in
add wave -noupdate -label {Output Peripherals} -radix hexadecimal /risc_tb/dut/out
add wave -noupdate -label RF -radix decimal /risc_tb/dut/rf
add wave -noupdate -divider ALU
add wave -noupdate -label Operation /risc_tb/dut/alu_op
add wave -noupdate -label SR /risc_tb/dut/sr
add wave -noupdate -label InA -radix decimal /risc_tb/dut/alu_inA
add wave -noupdate -label InB -radix decimal /risc_tb/dut/alu_inB
add wave -noupdate -label Out -radix hexadecimal /risc_tb/dut/alu_out
add wave -noupdate -label Extended -radix hexadecimal /risc_tb/dut/alu_ext
add wave -noupdate -divider MM
add wave -noupdate -label PC -radix hexadecimal /risc_tb/dut/pc
add wave -noupdate -label SP -radix hexadecimal /risc_tb/dut/sp
add wave -noupdate -label Write /risc_tb/dut/mm_wr
add wave -noupdate -label {Addr Select} /risc_tb/dut/mm_addr_sel
add wave -noupdate -label Addr -radix hexadecimal /risc_tb/dut/mm_addr
add wave -noupdate -label In -radix decimal /risc_tb/dut/mm_in
add wave -noupdate -label Out -radix decimal /risc_tb/dut/mm_out
add wave -noupdate -divider BP
add wave -noupdate -radix unsigned /risc_tb/dut/bp_index
add wave -noupdate /risc_tb/dut/bp_table/bp_table
add wave -noupdate /risc_tb/dut/bp_wr
add wave -noupdate /risc_tb/dut/jmp_prediction
add wave -noupdate /risc_tb/dut/jmp_taken
add wave -noupdate -divider Misc.
add wave -noupdate /risc_tb/dut/stall
add wave -noupdate -radix unsigned /risc_tb/dut/ri
add wave -noupdate -radix unsigned /risc_tb/dut/rj
add wave -noupdate -radix binary -childformat {{{/risc_tb/dut/ir[0]} -radix binary} {{/risc_tb/dut/ir[1]} -radix binary} {{/risc_tb/dut/ir[2]} -radix binary} {{/risc_tb/dut/ir[3]} -radix binary}} -expand -subitemconfig {{/risc_tb/dut/ir[0]} {-height 15 -radix binary} {/risc_tb/dut/ir[1]} {-height 15 -radix binary} {/risc_tb/dut/ir[2]} {-height 15 -radix binary} {/risc_tb/dut/ir[3]} {-height 15 -radix binary}} /risc_tb/dut/ir
add wave -noupdate -radix hexadecimal /risc_tb/dut/ma_base
add wave -noupdate -radix hexadecimal /risc_tb/dut/ma_offset
add wave -noupdate -radix hexadecimal /risc_tb/dut/ma_eff
add wave -noupdate -divider Functions
add wave -noupdate -radix decimal /risc_tb/dut/resolve_forward/resolve_forward
add wave -noupdate /risc_tb/dut/wb_from_alu/wb_from_alu
add wave -noupdate /risc_tb/dut/wb_both_from_alu/wb_both_from_alu
TreeUpdate [SetDefaultTree]
WaveRestoreCursors {{Cursor 1} {1121215 ps} 0}
quietly wave cursor active 1
configure wave -namecolwidth 135
configure wave -valuecolwidth 100
configure wave -justifyvalue left
configure wave -signalnamewidth 1
configure wave -snapdistance 10
configure wave -datasetprefix 0
configure wave -rowmargin 4
configure wave -childrowmargin 2
configure wave -gridoffset 0
configure wave -gridperiod 1
configure wave -griddelta 40
configure wave -timeline 0
configure wave -timelineunits ps
update
WaveRestoreZoom {820257 ps} {1312429 ps}
