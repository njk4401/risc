use phf_macros::phf_map;

static OPCODES: phf::Map<&'static str, u8> = phf_map! {
    "nop"  => 0b111111,

    // Data Manipulations
    "not"  => 0b000000,
    "and"  => 0b000001,
    "or"   => 0b000010,
    "xor"  => 0b000011,
    "shra" => 0b000100,
    "shrl" => 0b000101,
    "rotr" => 0b000110,
    "rotl" => 0b000111,
    "add"  => 0b001000,
    "addc" => 0b001001,
    "sub"  => 0b001010,
    "subc" => 0b001011,
    "mul"  => 0b001100,
    "div"  => 0b001101,
    "cpy"  => 0b001110,

    // Flow Control
    "jmp"  => 0b100000,
    "call" => 0b100001,
    "ret"  => 0b100010,

    // Data Transfer
    "ld"   => 0b100100,
    "st"   => 0b100101,
    "push" => 0b100110,
    "pop"  => 0b100111,

    // Extra
    "cmp"  => 0b110000,
    "cmpc" => 0b110001
};
