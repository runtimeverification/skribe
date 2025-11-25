#![cfg_attr(not(any(test, feature = "export-abi")), no_main)]
extern crate alloc;

use stylus_sdk::{alloy_primitives::U256, prelude::*};

use crate::skribe::{build_init_code, new_cheatcodes};

mod skribe;

sol_interface! {
  interface ICounter {
      function number() external returns (uint256);
      function setNumber(uint256) external;
      function increment() external;
  }
}

// `Counter` will be the entrypoint.
sol_storage! {
    #[entrypoint]
    pub struct TestCounter {
        uint256 number;
        address counter;
    }
}

const COUNTER_BYTECODE_PATH: &str =
    "../stylus-hello-world/target/wasm32-unknown-unknown/release/stylus_hello_world.wasm";

#[public]
impl TestCounter {
    pub fn setUp(&mut self) {
        self.number.set(U256::from(123));

        let cheatcodes = new_cheatcodes();

        let bytecode = cheatcodes
            .read_file_binary(&mut *self, COUNTER_BYTECODE_PATH.to_string())
            .unwrap();
        let counter_address = unsafe {
            self.vm()
                .deploy(&build_init_code(&bytecode), U256::ZERO, Option::None)
                .unwrap()
        };

        self.counter.set(counter_address);
    }

    pub fn test_self_number(&self) {
        assert_eq!(self.number.get(), U256::from(123));
    }

    pub fn test_call_set_get_number(&mut self, x: U256) {
        let counter = ICounter::new(self.counter.get());
        counter.set_number(&mut *self, x).unwrap();

        assert_eq!(counter.number(self).unwrap(), x);
    }

    pub fn test_call_increment(&mut self, x: U256) {
        if x >= U256::MAX {
            return;
        }

        let counter = ICounter::new(self.counter.get());
        counter.set_number(&mut *self, x).unwrap();
        counter.increment(&mut *self).unwrap();

        assert_eq!(counter.number(self).unwrap(), x + U256::from(1));
    }

    pub fn test_add_comm(&self, first: U256, second: U256) {
        let a = first.checked_add(second);
        let b = second.checked_add(first);

        assert_eq!(a, b);
    }
}
