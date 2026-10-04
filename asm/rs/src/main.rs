// mod syntax;

use clap::Parser;


#[derive(Parser, Debug)]
#[command(version, about, long_about=None)]
struct Args {
    #[arg(help="Paths to assembly source files")]
    files: Vec<String>,

    #[arg(short, long, default_value="", help="Path to output file")]
    output: String,

    #[arg(long, default_value_t=0xFFFF, help="Maximum on-chip memory depth")]
    mem_depth: u16
}


fn main() {
    let args: Args = Args::parse();
    println!("{args:?}");
}
