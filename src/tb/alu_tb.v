`timescale 1ps / 1ps

module alu_tb;

`include "../../include/opcodes.vh"
`include "../../include/status.vh"

/*===========================================================================*\
| DUT Signals
\*===========================================================================*/
reg  [4:0] opcode;
reg [15:0] inA;
reg [15:0] inB;

wire  [3:0] cnvz;
wire [16:0] result;
wire [31:0] ext_result;

/*===========================================================================*\
| Internal Variables
\*===========================================================================*/
integer passed;
integer failed;

/*===========================================================================*\
| DUT Instance
\*===========================================================================*/
alu dut(
  .opcode     (opcode),
  .inA        (inA),
  .inB        (inB),
  .cnvz       (cnvz),
  .result     (result),
  .ext_result (ext_result)
);

/*===========================================================================*\
| Test Sequence
\*===========================================================================*/
initial begin
  $timeformat(-9, 2, "ns", 16);

  passed = 0;
  failed = 0;

  opcode = 0;
  inA = 0;
  inB = 0;

  #1;

  $display("========================");
  $display(" Starting ALU Testbench ");
  $display("========================");

  test_opcode(
    `OP_NOT,
    16'h0000,
    16'h0000,
    4'b1 << `NEGATIVE,
    17'h0FFFF,
    32'h0,
    "NOT 0000"
  );
  test_opcode(
    `OP_NOT,
    16'hFFFF,
    16'h0,
    4'b1 << `ZERO,
    17'h0,
    32'h0,
    "NOT FFFF"
  );

  test_opcode(
    `OP_AND,
    16'hAAAA,
    16'h5555,
    4'b1 << `ZERO,
    17'h00000,
    32'h0,
    "AND"
  );
  test_opcode(
    `OP_AND,
    16'hFFFF,
    16'hBEEF,
    4'b1 << `NEGATIVE,
    17'h0BEEF,
    32'h0,
    "AND nonzero"
  );

  test_opcode(
    `OP_OR,
    16'hAAAA,
    16'h5555,
    4'b1 << `NEGATIVE,
    17'h0FFFF,
    32'h0,
    "OR"
  );

  test_opcode(
    `OP_XOR,
    16'hAAAA,
    16'h5555,
    4'b1 << `NEGATIVE,
    17'h0FFFF,
    32'h0,
    "XOR"
  );
  test_opcode(
    `OP_XOR,
    16'hAAAA,
    16'hAAAA,
    4'b1 << `ZERO,
    17'h00000,
    32'h0,
    "XOR zero"
  );

  test_opcode(
    `OP_SHRL,
    16'h8000,
    16'd1,
    4'b0000,
    17'h04000,
    32'h0,
    "SHRL"
  );

  test_opcode(
    `OP_SHRA,
    16'h8000,
    16'd1,
    4'b1 << `NEGATIVE,
    17'h0C000,
    32'h0,
    "SHRA negative"
  );
  test_opcode(
    `OP_SHRA,
    16'h4000,
    16'd1,
    4'b0000,
    17'h02000,
    32'h0,
    "SHRA positive"
  );

  test_opcode(
    `OP_ROTR,
    16'h8001,
    16'd1,
    1'b1 << `NEGATIVE,
    17'h0C000,
    32'h0,
    "ROTR"
  );

  test_opcode(
    `OP_ROTL,
    16'h8001,
    16'd1,
    4'b0000,
    17'h00003,
    32'h0,
    "ROTL"
  );

  test_opcode(
    `OP_ADD,
    16'hFFFF,
    16'h0001,
    (4'b1 << `CARRY) | (4'b1 << `ZERO),
    17'h10000,
    32'h0,
    "ADD carry"
  );
  test_opcode(
    `OP_ADD,
    16'h7FFF,
    16'h0001,
    (4'b1 << `NEGATIVE) | (4'b1 << `OVERFLOW),
    17'h08000,
    32'h0,
    "ADD overflow"
  );
  test_opcode(
    `OP_ADD,
    16'h8000,
    16'hFFFF,
    (4'b1 << `CARRY) | (4'b1 << `OVERFLOW),
    17'h17FFF,
    32'h0,
    "ADD underflow"
  );

  test_opcode(
    `OP_SUB,
    16'h0003,
    16'h0005,
    (4'b1 << `CARRY) | (4'b1 << `NEGATIVE),
    17'h1FFFE,
    32'h0,
    "SUB negative"
  );

  // Finish
  #1;
  $display("\n========================");
  $display(" ALU Testbench Complete");
  if(failed > 0) $display(" Result: FAIL");
  else $display(" Result: PASS");
  $display(" TEST SUMMARY");
  $display("  Passed: %0d", passed);
  $display("  Failed: %0d", failed);
  $display("========================");
  $stop;
end

/*===========================================================================*\
| OpCode Test Task
\*===========================================================================*/
task test_opcode;
  input   [4:0] test_opcode;
  input  [15:0] test_A;
  input  [15:0] test_B;
  input   [3:0] expected_cnvz;
  input  [16:0] expected_result;
  input  [31:0] expected_ext;
  input [127:0] msg;

  begin
    opcode = test_opcode;
    inA = test_A;
    inB = test_B;

    #1;

    if(
      (result !== expected_result)  ||
      (ext_result !== expected_ext) ||
      (cnvz !== expected_cnvz)
    ) begin
      failed = failed + 1;
      $display("\nFAIL: %s", msg);
      $display("\tA    = %h", test_A);
      $display("\tB    = %h", test_B);
      $display("\tcnvz = %b (expected %b)", cnvz, expected_cnvz);
      $display("\tres  = %h (expected %h)", result, expected_result);
      $display("\text  = %h (expected %h)", ext_result, expected_ext);
    end else begin
      passed = passed + 1;
      $display("\nPASS: %s", msg);
    end
  end
endtask

endmodule
