//=====================================================
// Jump Condition Definitions
//=====================================================

`ifndef JMPCONDS_H
`define JMPCONDS_H

`define JMP_U  5'b00000  // Unconditional
`define JMP_C1 5'b00001  // If Carry
`define JMP_N1 5'b00010  // If Negative
`define JMP_V1 5'b00011  // If Overflow
`define JMP_Z1 5'b00100  // If Zero
`define JMP_C0 5'b00101  // If ~Carry
`define JMP_N0 5'b00110  // If ~Negative
`define JMP_V0 5'b00111  // If ~Overflow
`define JMP_Z0 5'b01000  // If ~Zero

`endif
