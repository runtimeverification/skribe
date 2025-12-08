#![cfg_attr(not(any(test, feature = "export-abi")), no_main)]
extern crate alloc;

use stylus_sdk::{
    alloy_primitives::{address, FixedBytes, U256},
    prelude::*,
};

use skribe::cheat;

sol_storage! {
    #[entrypoint]
    pub struct TestCheatcodes {
        uint256 number;
    }
}

#[public]
impl TestCheatcodes {
    pub fn set_up(&mut self) {
        self.number.set(U256::from(123));
    }

    pub fn test_deal(&mut self) {
        let alice = address!("AABBCCDDEEFF0011223344556677889900AABBCC");
        assert_eq!(self.vm().balance(alice), U256::ZERO);

        let balance = U256::from(123000000000u128);
        cheat().deal(&mut *self, alice, balance).unwrap();

        assert_eq!(self.vm().balance(alice), balance);
    }

    pub fn test_env_getter_setters(&mut self) {
        // contract_address
        let expected = address!("7FA9385BE102AC3EAC297483DD6233D62B3E1496"); // predefined address for test contracts
        assert_eq!(expected, self.vm().contract_address());

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
