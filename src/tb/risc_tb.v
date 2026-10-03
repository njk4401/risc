/*****************************************************************************\
| File: risc_tb.v
| Description: Testbench for the RISC module.
\*****************************************************************************/
`timescale 1ps / 1ps

`include "../../iw2ascii.v"

module risc_tb;

/*===========================================================================*\
| DUT Parameters
\*===========================================================================*/
localparam RF_SIZE = 5'd7;
localparam IO_WIDTH = 4'd1;
localparam PM_DEPTH = 16'h7FFF;
localparam MM_INIT = "../../etc/arith_test.mif";

/*===========================================================================*\
| DUT Signals
\*===========================================================================*/
reg rst;
reg clk;
reg  [((2**IO_WIDTH)*16)-1:0] in;
wire [((2**IO_WIDTH)*16)-1:0] out;

/*===========================================================================*\
| I/O Peripherals
\*===========================================================================*/


/*===========================================================================*\
| DUT Instance
\*===========================================================================*/
risc#(
  .RF_SIZE  (RF_SIZE),
  .IO_WIDTH (IO_WIDTH),
  .PM_DEPTH (PM_DEPTH),
  .MM_INIT  (MM_INIT)
) dut(
  .rst (rst),
  .clk (clk),
  .in  (in),
  .out (out)
);

/*===========================================================================*\
| Internal Variables
\*===========================================================================*/
wire [255:0] iw0;
wire [255:0] iw1;
wire [255:0] iw2;
wire [255:0] iw3;

wire [2048:0] wave_msg;

assign wave_msg = (!rst)          ? "Reset"                   :
                //(!DUT.pm_ready) ? "Resolving PM Cache Miss" :
                  "Running Program";

/*===========================================================================*\
| IW Decoders
\*===========================================================================*/
iw2ascii iw0_translate(
  .iw    (dut.mm_out),
  .ascii (iw0)
);
iw2ascii iw1_translate(
  .iw    (dut.ir[1]),
  .ascii (iw1)
);
iw2ascii iw2_translate(
  .iw    (dut.ir[2]),
  .ascii (iw2)
);
iw2ascii iw3_translate(
  .iw    (dut.ir[3]),
  .ascii (iw3)
);

/*===========================================================================*\
| Clock Generation
\*===========================================================================*/
always #20000 clk = ~clk;

/*===========================================================================*\
| Test Sequence
\*===========================================================================*/
initial begin
  $timeformat(-9, 2, "ns", 16);

  // Initialize inputs
  clk = 1'b0;
  in = {((2**IO_WIDTH)*16){1'b0}};

  // Hold reset
  rst = 1'b0;
  repeat(5) @(posedge clk);
  rst = 1'b1;

  repeat(40) @(posedge clk);
  $stop;
end

/*===========================================================================*\
| Wait for end of program
\*===========================================================================*/
always @(*) if(dut.pc == PM_DEPTH) begin
  $display("%t Reached end of program!", $time);
  repeat(5) @(posedge clk);
  $stop;
end

endmodule
