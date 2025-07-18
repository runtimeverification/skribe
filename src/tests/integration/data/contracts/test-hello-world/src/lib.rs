#![cfg_attr(not(any(test, feature = "export-abi")), no_main)]
extern crate alloc;

use stylus_sdk::{
    alloy_primitives::{Address, U256},
    call::Call,
    prelude::*,
};

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

#[public]
impl TestCounter {
    pub fn init(&mut self, counter: Address) {
        self.number.set(U256::from(123));
        self.counter.set(counter);
    }

    pub fn test_self_number(&self) {
        assert_eq!(self.number.get(), U256::from(123));
    }

    pub fn test_call_set_get_number(&mut self, x: U256) -> bool {
        let counter = ICounter::new(self.counter.get());
        counter.set_number(Call::new_in(self), x).unwrap();

        counter.number(self).unwrap() == x
    }

    pub fn test_call_increment(&mut self, x: U256) -> bool {
        if x >= U256::MAX {
            return true;
        }

        let counter = ICounter::new(self.counter.get());
        counter.set_number(Call::new_in(self), x).unwrap();
        counter.increment(Call::new_in(self)).unwrap();

        counter.number(self).unwrap() == x + U256::from(1)
    }

    pub fn test_add_comm(&self, first: U256, second: U256) -> bool {
        let a = first.checked_add(second);
        let b = second.checked_add(first);

        a == b
    }
}
