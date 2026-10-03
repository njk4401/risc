/*****************************************************************************\
| File: risc.v
| Specs: 16-bit | Von Neumann Architecture | Memory Mapped I/O-P
\*****************************************************************************/
`timescale 1ps / 1ps

module risc#(
  parameter RF_SIZE = 5'd31,  // Number of registers in the register file
  parameter IO_WIDTH = 4'd6,  // Number of bits allocated to I/O-P's
  parameter PM_DEPTH = 16'h7FFF,  // Depth of program memory
  parameter MM_INIT = "../etc/init.mif"  // Main memory initialization file
)(
  input rst,  // Synchronous reset
  input clk,  // Clock
  input      [((2**IO_WIDTH)*16)-1:0] in,  // Input peripheral bus
  output reg [((2**IO_WIDTH)*16)-1:0] out  // Output peripheral bus
);

// Definitions
`include "../include/status.vh"
`include "../include/opcodes.vh"
`include "../include/jmpconds.vh"
`include "../include/addrmodes.vh"

// Don't Care State
localparam DNC = 16'hFFFF;
// Address for the top of stack
localparam TOS = 16'hFFFF - (16'b1 << IO_WIDTH);

// Memory Address Select
localparam MM_ADDR_PC = 2'b00;
localparam MM_ADDR_SP = 2'b01;
localparam MM_ADDR_MA = 2'b10;

// Looping variable
integer i;

/*===========================================================================*\
| Internal Signals
\*===========================================================================*/
reg [15:0] rf[0:RF_SIZE];         // Register File
reg [15:0] pc;                    // Program Counter
reg [15:0] sp;                    // Stack Pointer
reg  [3:0] sr;                    // Status Register
reg [15:0] shadow_rf[0:RF_SIZE];  // Shadow Register File
reg [15:0] shadow_pc;             // Shadow Program Counter
reg [15:0] shadow_sp;             // Shadow Stack Pointer
reg  [3:0] shadow_sr;             // Shadow Status Register

reg [15:0] ma_base;    // Base Memory Address
reg [15:0] ma_offset;  // Memory Address Offset
reg [15:0] ma_eff;     // Effective Memory Address

reg   [4:0] alu_op;   // ALU Operation
reg  [15:0] alu_inA;  // ALU Input A
reg  [15:0] alu_inB;  // ALU Input B
wire  [3:0] alu_sr;   // ALU Status
wire [16:0] alu_out;  // ALU Output
wire [31:0] alu_ext;  // Extended ALU Output

reg         mm_wr;        // Main Memory Write Enable
reg  [15:0] mm_in;        // Main Memory Input
reg   [2:0] mm_addr_sel;  // Main Memory Address Select
wire        access_io;    // Whether Accessing Mem-Mapped I/O
wire [15:0] mm_addr;      // Main Memory Address
wire [15:0] mm_out;       // Main Memory Output

reg        stall[0:3];
reg  [4:0] ri[1:3];
reg  [4:0] rj[1:3];
reg [15:0] ir[1:3];  // Instruction Register File

wire n_clk;

assign access_io = &mm_addr[15:IO_WIDTH];
assign mm_addr   = (mm_addr_sel == MM_ADDR_PC) ? pc     :
                   (mm_addr_sel == MM_ADDR_SP) ? sp     :
                   (mm_addr_sel == MM_ADDR_MA) ? ma_eff :
                   16'b0;

/*===========================================================================*\
| Structural Instantiations
\*===========================================================================*/
// Clock Inverter
not clock_inv(n_clk, clk);

// Main Memory
ram16#(.init_file (MM_INIT)) mm(
  .address (mm_addr),
  .clock   (n_clk),
  .data    (mm_in),
  .wren    (mm_wr),
  .q       (mm_out)
);

// Function Unit
alu fu(
  .opcode     (alu_op),
  .inA        (alu_inA),
  .inB        (alu_inB),
  .cnvz       (alu_sr),
  .result     (alu_out),
  .ext_result (alu_ext)
);

/*===========================================================================*\
| Procedural Description
\*===========================================================================*/
always @(posedge clk) begin: cpu
  /*=========================================================================*\
  | Synchronous Reset
  \*=========================================================================*/
  if(!rst) begin
    // Clear register file
    for(i = 0; i < RF_SIZE+1; i = i+1) begin
      rf[i] = 16'b0;
    end

    // Initialize all internal signals
    sp          = TOS;
    sr          =  4'b0;
    pc          = 16'b0;
    ma_base     = 16'b0;
    ma_offset   = 16'b0;
    ma_eff      = 16'b0;
    alu_op      =  5'b0;
    alu_inA     = 16'b0;
    alu_inB     = 16'b0;
    mm_wr       =  1'b0;
    mm_in       = 16'b0;
    mm_addr_sel = MM_ADDR_PC;

    stall[0] = 1'b0;
    for(i = 1; i <= 3; i = i+1) begin
      stall[i] = 1'b0;
      ri[i]    = 5'b0;
      rj[i]    = 5'b0;
      ir[i]    = DNC;
    end

    // Drive all output peripherals low
    out = {(2**IO_WIDTH){16'b0}};
  end

  /*=========================================================================*\
  | Normal Operation
  \*=========================================================================*/
  else begin
    if(!stall[3] && (ir[3] != DNC)) begin
      case(ir[3][15:10])
        `OP_NOT, `OP_AND, `OP_OR, `OP_XOR,
        `OP_SHRA, `OP_SHRL, `OP_ROTR, `OP_ROTL,
        `OP_ADD, `OP_ADDC, `OP_SUB, `OP_SUBC, `OP_MUL, `OP_DIV,
        `OP_CPY: begin end

        `OP_LD: begin
          if(access_io)
            rf[ri[3]] = in[mm_addr[IO_WIDTH-1:0]*16 +: 16];
          else
            rf[ri[3]] = mm_out;
          mm_addr_sel = MM_ADDR_PC;
        end

        `OP_ST: begin
          mm_wr = 1'b0;
          mm_addr_sel = MM_ADDR_PC;
        end

        `OP_JMP: begin
          case(ri[3])
            `JMP_C1: if(sr[`CARRY])     pc = ma_eff;
            `JMP_N1: if(sr[`NEGATIVE])  pc = ma_eff;
            `JMP_V1: if(sr[`OVERFLOW])  pc = ma_eff;
            `JMP_Z1: if(sr[`ZERO])      pc = ma_eff;
            `JMP_C0: if(!sr[`CARRY])    pc = ma_eff;
            `JMP_N0: if(!sr[`NEGATIVE]) pc = ma_eff;
            `JMP_V0: if(!sr[`OVERFLOW]) pc = ma_eff;
            `JMP_Z0: if(!sr[`ZERO])     pc = ma_eff;
            `JMP_U:  pc = ma_eff;
            default: pc = pc;
          endcase
        end

        `OP_CALL: begin
          mm_wr = 1'b0;
          pc = ma_eff;
          mm_addr_sel = MM_ADDR_PC;
        end

        `OP_RET: begin
          pc = mm_out;
          mm_addr_sel = MM_ADDR_PC;
        end

        `OP_NOP: begin end
      endcase
    end  // MC3

    if(!stall[2] && (ir[2] != DNC)) begin
      case(ir[2][15:10])
        `OP_NOT, `OP_AND, `OP_OR, `OP_XOR,
        `OP_SHRA, `OP_SHRL, `OP_ROTR, `OP_ROTL,
        `OP_ADD, `OP_ADDC, `OP_SUB, `OP_SUBC,
        `OP_CPY: begin
          rf[ri[2]] = alu_out[15:0];
          sr = alu_sr;
        end

        `OP_MUL, `OP_DIV: begin
          rf[ri[2]] = alu_ext[15:0];
          rf[rj[2]] = alu_ext[31:16];
          sr = alu_sr;
        end

        `OP_LD: begin
          ma_eff = ma_base + ma_offset;
          mm_addr_sel = MM_ADDR_MA;
        end

        `OP_ST: begin
          ma_eff = ma_base + ma_offset;
          if(access_io) begin
            out[mm_addr[IO_WIDTH-1:0]*16 +: 16] = rf[ri[2]];
          end else begin
            mm_addr_sel = MM_ADDR_MA;
            mm_wr = 1'b1;
            mm_in = rf[ri[2]];
          end
        end

        `OP_JMP: begin
          ma_eff = ma_base + ma_offset;
        end

        `OP_CALL: begin
          ma_eff = ma_base + ma_offset;
          mm_in = {12'b0, SR};
          sp = sp - 1'b1;
        end

        `OP_RET: begin
          sr = mm_out[3:0];
          sp = sp + 1'b1;
        end

        `OP_NOP: begin end
      endcase
    end  // MC2

    if(!stall[1] && (ir[1] != DNC)) begin
      case(ir[1][15:10])
        // 1-Source Manipulations
        `OP_NOT,
        `OP_SHRA, `OP_SHRL, `OP_ROTR, `OP_ROTL,
        `OP_ADDC, `OP_SUBC,
        `OP_CPY: begin
          alu_op  = ir[1][14:10];
          alu_inA = resolve_forward(ri[1]);
          alu_inB = {11'b0, rj[1]};
        end

        // 2-Source Manipulations
        `OP_AND, `OP_OR, `OP_XOR,
        `OP_ADD, `OP_SUB, `OP_MUL, `OP_DIV: begin
          alu_op  = ir[1][14:10];
          alu_inA = resolve_forward(ri[1]);
          alu_inB = resolve_forward(rj[1]);
        end

        // Address Fetching
        `OP_LD, `OP_ST, `OP_JMP: begin
          ma_base = mm_out;
          ma_offset = resolve_addr_mode(rj[1]);
          pc = pc + 1'b1;
        end

        `OP_CALL: begin
          ma_base = mm_out;
          ma_offset = resolve_addr_mode(rj[1]);
          pc = pc + 1'b1;
          mm_wr = 1'b1;
          mm_addr_sel = MM_ADDR_SP;
          mm_in = pc;
          sp = sp - 1'b1;
        end

        `OP_RET: begin
          sp = sp + 1'b1;
          mm_addr_sel = MM_ADDR_SP;
        end

        `OP_NOP: begin end
      endcase
    end  // MC1

    /*-----------------------------------------------------------------------*\
    | Machine Cycle 0
    \*-----------------------------------------------------------------------*/
    if(!stall[2] && !is_flow_ctrl(ir[3][15:10])) begin
      ir[3] = ir[2];
      ri[3] = ri[2];
      rj[3] = rj[2];
      stall[3] = 1'b0;
    end else begin
      stall[2] = 1'b1;
      ir[3] = DNC;
    end

    if(!stall[1] && !is_flow_ctrl(ir[2][15:10])) begin
      ir[2] = ir[1];
      ri[2] = ri[1];
      rj[2] = rj[1];
      stall[2] = 1'b0;
    end else begin
      stall[1] = 1'b1;
      ir[2] = DNC;
    end

    if(!stall[0] && !is_multiple_iw(ir[1][15:10])) begin
      ir[1] = mm_out;
      ri[1] = mm_out[9:5];
      rj[1] = mm_out[4:0];
      pc = pc + 1'b1;
      stall[1] = 1'b0;
    end else begin
      stall[0] = 1'b1;
      ir[1] = DNC;
    end

    if(ir[3] == DNC && !is_multiple_iw(ir[2][15:10])) begin
      stall[0] = 1'b0;
    end
  end  // Normal operation
end  // CPU


function is_multiple_iw;
  input [5:0] opcode;

  begin
    is_multiple_iw = (opcode == `OP_LD)   ||
                     (opcode == `OP_ST)   ||
                     (opcode == `OP_JMP)  ||
                     (opcode == `OP_CALL);
  end
endfunction

function is_flow_ctrl;
  input [5:0] opcode;

  begin
    is_flow_ctrl = (opcode == `OP_JMP)  ||
                   (opcode == `OP_CALL) ||
                   (opcode == `OP_RET);
  end
endfunction

function wb_from_alu;
  input [5:0] opcode;

  begin
    wb_from_alu = !opcode[5];
  end
endfunction

function wb_both_from_alu;
  input [5:0] opcode;

  begin
    wb_both_from_alu = (opcode == `OP_MUL) || (opcode == `OP_DIV);
  end
endfunction

function [15:0] resolve_forward;
  input [4:0] r;

  begin
    if(wb_both_from_alu(ir[2][15:10])) begin
      resolve_forward = (r == ri[2]) ? alu_ext[15:0]  :
                        (r == rj[2]) ? alu_ext[31:16] :
                        rf[r];
    end

    else if(wb_from_alu(ir[2][15:10])) begin
      resolve_forward = (r == ri[2]) ? alu_out[15:0] : rf[r];
    end

    else begin
      resolve_forward = rf[r];
    end
  end
endfunction

function [15:0] resolve_addr_mode;
  input [4:0] r;

  begin
    case(r)
      `AM_DIRECT: resolve_addr_mode = 16'b0;
      `AM_PCREL:  resolve_addr_mode = pc;
      `AM_SPREL:  resolve_addr_mode = sp;
      default:    resolve_addr_mode = resolve_forward(r);
    endcase
  end
endfunction

endmodule
