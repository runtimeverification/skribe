#![cfg_attr(not(any(test, feature = "export-abi")), no_main)]
extern crate alloc;

use stylus_sdk::{alloy_primitives::U256, prelude::*};

sol_interface! {
    interface ICounter {
        function number() external returns (uint256);
        function increment() external;
    }
}

#[storage]
#[entrypoint]
pub struct CallCounter;

#[public]
impl CallCounter {
    // Gets the number from a counter contract.
    pub fn number(&mut self, counter: ICounter) -> U256 {
        counter.number(self).unwrap()
    }

    pub fn increment(&mut self, counter: ICounter) {
        counter.increment(self).unwrap()
    }
}
