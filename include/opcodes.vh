//=====================================================
// OpCode Definitions
//=====================================================

`ifndef OPCODES_H
`define OPCODES_H

`define OP_NOP  6'b111111  // No Operation

// ALU Instructions
`define OP_NOT  6'b000000  // Bitwise Invert
`define OP_AND  6'b000001  // Bitwise AND
`define OP_OR   6'b000010  // Bitwise OR
`define OP_XOR  6'b000011  // Bitwise XOR
`define OP_SHRA 6'b000100  // Shift Right Arithmetic
`define OP_SHRL 6'b000101  // Shift Right Logic
`define OP_ROTR 6'b000110  // Rotate Right
`define OP_ROTL 6'b000111  // Rotate Left
`define OP_ADD  6'b001000  // Addition
`define OP_ADDC 6'b001001  // Addition with Constant
`define OP_SUB  6'b001010  // Subtraction
`define OP_SUBC 6'b001011  // Subtraction with Constant
`define OP_MUL  6'b001100  // Multiplication
`define OP_DIV  6'b001101  // Division
`define OP_CPY  6'b001110  // Copy
`define OP_RRC  6'b010000  // Rotate Right through Carry
`define OP_RLC  6'b010001  // Rotate Left through Carry

// Flow Control
`define OP_JMP  6'b100000  // Jump
`define OP_CALL 6'b100001  // Call
`define OP_RET  6'b100010  // Return

// Data Transfer
`define OP_LD   6'b100100  // Load
`define OP_ST   6'b100101  // Store
`define OP_PUSH 6'b100110  // Push to stack
`define OP_POP  6'b100111  // Pop from stack

// Extra
`define OP_CMP  6'b110000  // Compare
`define OP_CMPC 6'b110001  // Compare with Constant

`endif
