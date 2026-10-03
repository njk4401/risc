`timescale 1ps / 1ps

module alu(
  input  [4:0] opcode,     // Operation Code
  input [15:0] inA,        // Input A
  input [15:0] inB,        // Input B
  output reg [3:0] cnvz,       // Status Bits
  output reg [16:0] result,     // Result
  output reg [31:0] ext_result  // Extended Result
);

// Definitions
`include "../include/opcodes.vh"
`include "../include/status.vh"

wire [31:0] mul_result;  // Multiplier Result
wire [31:0] div_result;  // Divider Result

// Multiply and Divide Units
mul16 mul_unit(
  .dataa  (inA),        // Input <- Operand A
  .datab  (inB),        // Input <- Operand B
  .result (mul_result)  // Output -> Result of A*B
);
div16 div_unit(
  .numer    (inA),                // Input <- Operand A
  .denom    (inB),                // Input <- Operand B
  .quotient (div_result[15:0]),  // Output -> Result of A/B
  .remain   (div_result[31:16])  // Output -> Result of A%B
);

always @(*) begin
  result = 16'b0;
  ext_result = 16'b0;
  case(opcode)
    `OP_NOT:  result[15:0] = ~inA;
    `OP_AND:  result[15:0] = inA & inB;
    `OP_OR:   result[15:0] = inA | inB;
    `OP_XOR:  result[15:0] = inA ^ inB;
    `OP_SHRA: result[15:0] = $signed(inA) >>> inB;
    `OP_SHRL: result[15:0] = inA >> inB;
    `OP_ROTR: result[15:0] = (inA >> inB) | (inA << (5'd16 - inB));
    `OP_ROTL: result[15:0] = (inA << inB) | (inA >> (5'd16 - inB));
    `OP_CPY:  result[15:0] = inA;
    `OP_MUL:  ext_result = mul_result;
    `OP_DIV:  ext_result = div_result;
    `OP_ADD, `OP_ADDC: result = inA + inB;
    `OP_SUB, `OP_SUBC: result = inA - inB;
    `OP_RRC: begin
      result = ({cnvz[`CARRY], inA} >> inB) |
               ({cnvz[`CARRY] << (5'd17 - inB)});
    end
    `OP_RLC: begin
      result = ({cnvz[`CARRY], inA} << inB) |
               ({cnvz[`CARRY] >> (5'd17 - inB)});
    end
    default: begin
      result = result;
      ext_result = ext_result;
    end
  endcase
end

always @(*) begin
  cnvz = 3'b0;
  case(opcode)
    `OP_NOT, `OP_AND, `OP_OR, `OP_XOR,
    `OP_SHRA, `OP_SHRL, `OP_ROTR, `OP_ROTL: begin
      cnvz[`NEGATIVE] = result[15];
      cnvz[`ZERO] = ~|result[15:0];
    end

    `OP_MUL, `OP_DIV: begin
      cnvz[`NEGATIVE] = ext_result[15];
      cnvz[`ZERO] = ~|ext_result;
    end

    `OP_ADD, `OP_ADDC: begin
      cnvz[`CARRY] = result[16];
      cnvz[`NEGATIVE] = result[15];
      cnvz[`OVERFLOW] = (inA[15] &  inB[15] & !result[15]) |
                        (!inA[15] & !inB[15] &  result[15]);
      cnvz[`ZERO] = ~|result[15:0];
    end

    `OP_SUB, `OP_SUBC: begin
      cnvz[`CARRY] = result[16];
      cnvz[`NEGATIVE] = result[15];
      cnvz[`OVERFLOW] = (inA[15] & !inB[15] & !result[15]) |
                        (!inA[15] &  inB[15] &  result[15]);
      cnvz[`ZERO] = ~|result[15:0];
    end

    `OP_RRC, `OP_RLC: begin
      cnvz[`CARRY] = result[16];
    end

    default: cnvz = cnvz;
  endcase
end

endmodule
