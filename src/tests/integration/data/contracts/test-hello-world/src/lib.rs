#![cfg_attr(not(any(test, feature = "export-abi")), no_main)]
extern crate alloc;

use stylus_sdk::{alloy_primitives::U256, prelude::*};

// `Counter` will be the entrypoint.
sol_storage! {
    #[entrypoint]
    pub struct Counter {
        uint256 number;
    }
}

#[public]
impl Counter {
    pub fn init(&mut self) {
        self.number.set(U256::from(123));
    }

    pub fn test_number(&self) {
        assert_eq!(self.number.get(), U256::from(123));
    }

    pub fn test_add_comm(&self, first: U256, second: U256) -> bool {
        let a = first.checked_add(second);
        let b = second.checked_add(first);
        
        a == b
    }

}
