transcript on
if {[file exists rtl_work]} {
	vdel -lib rtl_work -all
}
vlib rtl_work
vmap work rtl_work

vlog -vlog01compat -work work +incdir+//wsl.localhost/archlinux/root/riscs/risc/src {//wsl.localhost/archlinux/root/riscs/risc/src/bp.v}
vlog -vlog01compat -work work +incdir+//wsl.localhost/archlinux/root/riscs/risc/ip {//wsl.localhost/archlinux/root/riscs/risc/ip/div16.v}
vlog -vlog01compat -work work +incdir+//wsl.localhost/archlinux/root/riscs/risc/ip {//wsl.localhost/archlinux/root/riscs/risc/ip/mul16.v}
vlog -vlog01compat -work work +incdir+//wsl.localhost/archlinux/root/riscs/risc/ip {//wsl.localhost/archlinux/root/riscs/risc/ip/ram16.v}
vlog -vlog01compat -work work +incdir+//wsl.localhost/archlinux/root/riscs/risc/src {//wsl.localhost/archlinux/root/riscs/risc/src/risc.v}
vlog -vlog01compat -work work +incdir+//wsl.localhost/archlinux/root/riscs/risc/src {//wsl.localhost/archlinux/root/riscs/risc/src/alu.v}

vlog -vlog01compat -work work +incdir+//wsl.localhost/archlinux/root/riscs/risc/src/tb {//wsl.localhost/archlinux/root/riscs/risc/src/tb/risc_tb.v}

vsim -t 1ps -L altera_ver -L lpm_ver -L sgate_ver -L altera_mf_ver -L altera_lnsim_ver -L cycloneive_ver -L rtl_work -L work -voptargs="+acc"  risc_tb

add wave *
view structure
view signals
run -all
