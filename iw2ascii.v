/*****************************************************************************\
| File: iw2ascii.v
| Description: Convert IW information into a string of ASCII characters.
\*****************************************************************************/

module iw2ascii(
  input [15:0] iw,
  output reg [255:0] ascii
);

`include "include/opcodes.vh"
`include "include/jmpconds.vh"
`include "include/addrmodes.vh"

localparam [15:0] DNC = 16'hFFFF;

wire [5:0] opcode;
wire [4:0] ri;
wire [4:0] rj;

assign {opcode, ri, rj} = iw;

reg [7:0] sbit;
reg [7:0] sbit_val;
reg [39:0] addr_mode;

always @(*) begin
  if(iw == DNC) begin
    ascii = "STALL";
  end

  else begin
    case(ri)
      `JMP_U:  begin sbit = "U"; sbit_val = "x"; end
      `JMP_C1: begin sbit = "C"; sbit_val = "1"; end
      `JMP_N1: begin sbit = "N"; sbit_val = "1"; end
      `JMP_V1: begin sbit = "V"; sbit_val = "1"; end
      `JMP_Z1: begin sbit = "Z"; sbit_val = "1"; end
      `JMP_C0: begin sbit = "C"; sbit_val = "0"; end
      `JMP_N0: begin sbit = "N"; sbit_val = "0"; end
      `JMP_V0: begin sbit = "V"; sbit_val = "0"; end
      `JMP_Z0: begin sbit = "Z"; sbit_val = "0"; end
    endcase

    case(rj)
      `AM_DIRECT: addr_mode = "#";
      `AM_PCREL:  addr_mode = "&";
      `AM_SPREL:  addr_mode = "$";
      default:    addr_mode = {"R", itoa(rj), "[]"};
    endcase

    case(opcode)
      `OP_NOT:  ascii = {"NOT  R", itoa(ri)};
      `OP_AND:  ascii = {"AND  R", itoa(ri), ", R", itoa(rj)};
      `OP_OR:   ascii = {"OR   R", itoa(ri), ", R", itoa(rj)};
      `OP_XOR:  ascii = {"XOR  R", itoa(ri), ", R", itoa(rj)};
      `OP_SHRA: ascii = {"SHRA R", itoa(ri), ", #", itoa(rj)};
      `OP_SHRL: ascii = {"SHRL R", itoa(ri), ", #", itoa(rj)};
      `OP_ROTR: ascii = {"ROTR R", itoa(ri), ", #", itoa(rj)};
      `OP_ROTL: ascii = {"ROTL R", itoa(ri), ", #", itoa(rj)};
      `OP_ADD:  ascii = {"ADD  R", itoa(ri), ", R", itoa(rj)};
      `OP_SUB:  ascii = {"SUB  R", itoa(ri), ", R", itoa(rj)};
      `OP_MUL:  ascii = {"MUL  R", itoa(ri), ", R", itoa(rj)};
      `OP_DIV:  ascii = {"DIV  R", itoa(ri), ", R", itoa(rj)};
      `OP_ADDC: ascii = {"ADDC R", itoa(ri), ", #", itoa(rj)};
      `OP_SUBC: ascii = {"SUBC R", itoa(ri), ", #", itoa(rj)};
      `OP_CMP:  ascii = {"CMP  R", itoa(ri), ", R", itoa(rj)};
      `OP_CMPC: ascii = {"CMPC R", itoa(ri), ", #", itoa(rj)};
      `OP_CPY:  ascii = {"CPY  R", itoa(ri), ", R", itoa(rj)};
      `OP_PUSH: ascii = {"PUSH R", itoa(ri)};
      `OP_POP:  ascii = {"POP  R", itoa(ri)};
      `OP_LD:   ascii = {"LD   R", itoa(ri), ", ", addr_mode};
      `OP_ST:   ascii = {"ST   R", itoa(ri), ", ", addr_mode};
      `OP_JMP:  ascii = {"JMP  ", addr_mode, ", if ", sbit, "=", sbit_val};
      `OP_CALL: ascii = {"CALL ", addr_mode};
      `OP_RET:  ascii = {"RET"};
      `OP_NOP:  ascii = {"NOP"};
      default:  ascii = {"UNDEFINED"};
    endcase
  end
end

/*===========================================================================*\
| Function: itoa
| Description: Convert an integer to ascii representation
| Input:
|   5-bit integer value to convert
| Output:
|   16-bit ascii representation
\*===========================================================================*/
function [15:0] itoa;
  input [4:0] value;
  integer dig1;
  integer dig2;

  begin
    itoa = {"", ""};

    // If single digit
    if(value < 5'd10) begin
	    itoa[7:0] = 8'h30+value;
	  end
	  // If double digit
    else begin
      dig1 = value / 5'd10;
      dig2 = value % 5'd10;
      itoa[15:8] = 8'h30+dig1;
		  itoa[7:0] = 8'h30+dig2;
    end
  end
endfunction

endmodule
