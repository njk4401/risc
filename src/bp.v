/*****************************************************************************\
| File: bp.v
| Description: 2-bit branch prediction table.
\*****************************************************************************/
`timescale 1ps / 1ps

module bp#(
  parameter DEPTH = 4  // Number of bits allocated to indexing the table
)(
  input rst,               // Synchronous reset
  input clk,               // Clock
  input taken,             // Feedback for whether the branch was taken
  input update,            // Update prediction counter
  input [DEPTH-1:0] addr,  // Branch table input address
  output prediction        // Jump prediction
);

integer i;

reg [1:0] bp_table[2**DEPTH-1:0];

assign prediction = bp_table[addr][1];

always @(posedge clk) begin
  /*-------------------------------------------------------------------------*\
  | Synchronous Reset
  \*-------------------------------------------------------------------------*/
  if(!rst) begin
    for(i = 0; i < 2**DEPTH; i = i+1) begin
      bp_table[i] <= 2'b10;  // Initialize to weak taken
    end
  end  // Reset

  /*-------------------------------------------------------------------------*\
  | Normal Operation
  \*-------------------------------------------------------------------------*/
  else begin
    if(update) begin
      if(taken) begin
        // Saturated Addition
        if(~bp_table[addr]) bp_table[addr] <= bp_table[addr] + 1'b1;
      end else begin
        // Saturated Subtraction
        if(|bp_table[addr]) bp_table[addr] <= bp_table[addr] - 1'b1;
      end
    end  // Update
  end  // Normal Operation
end

endmodule
