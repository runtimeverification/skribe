#![cfg_attr(not(any(test, feature = "export-abi")), no_main)]
extern crate alloc;

use alloy_primitives::address;
use stylus_sdk::{alloy_primitives::U256, prelude::*};

use skribe::{build_init_code, cheat};

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
    pub fn set_up(&mut self) {
        self.number.set(U256::from(123));

        let bytecode = cheat()
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
        cheat().assume(&mut *self, x < U256::MAX).unwrap();

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

    pub fn test_deal(&mut self) {
        let alice = address!("AABBCCDDEEFF0011223344556677889900AABBCC");
        assert_eq!(self.vm().balance(alice), U256::ZERO);

        let balance = U256::from(123000000000u128);
        cheat().deal(&mut *self, alice, balance).unwrap();

        assert_eq!(self.vm().balance(alice), balance);
    }

    pub fn test_env_setters(&mut self) {
        // warp
        let time = 123000000000u64;
        cheat().warp(&mut *self, U256::from(time)).unwrap();
        assert_eq!(self.vm().block_timestamp(), time);
        
        // roll
        let block_number = 123;
        cheat().roll(&mut *self, U256::from(block_number)).unwrap();
        assert_eq!(self.vm().block_number(), block_number);
    }
}
