#![no_main]

use libfuzzer_sys::fuzz_target;

use skribe_fuzz_rs::{kllvm, make_dv};

fuzz_target!( init: {
    kllvm::init();
},
    |data: &[u8]| {
    let _ = make_dv();
    // fuzzed code goes here
});
