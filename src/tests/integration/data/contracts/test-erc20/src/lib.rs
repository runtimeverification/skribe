#![cfg_attr(not(any(test, feature = "export-abi")), no_main)]
extern crate alloc;

use stylus_sdk::{alloy_primitives::{Address, U256}, prelude::*};

use skribe::{build_init_code, cheat};

sol_interface! {
    interface IERC20 {
        function balanceOf(address owner) external view returns (uint256);
        function transfer(address to, uint256 value) external returns (bool);
        function mint(uint256 value) external;
    }
}

// `Counter` will be the entrypoint.
sol_storage! {
    #[entrypoint]
    pub struct TestERC20 {
        address erc20;
    }
}

const ERC20_PATH: &str =
    "../erc20/target/wasm32-unknown-unknown/release/erc20.wasm";

#[public]
impl TestERC20 {
    pub fn set_up(&mut self) {
        
        let bytecode = cheat()
            .read_file_binary(&mut *self, ERC20_PATH.to_string())
            .unwrap();

        let addr = unsafe {
            self.vm()
                .deploy(&build_init_code(&bytecode), U256::ZERO, Option::None)
                .unwrap()
        };

        self.erc20.set(addr);
    }

    pub fn test_transfer_enough_balance(&mut self, alex: Address, balance: U256, amount: U256) {
        let cheats = cheat();
        let self_address = self.vm().contract_address();

        cheats.assume(&mut *self,
            U256::ZERO < amount
         && amount <= balance
        ).unwrap();

        let erc20 = IERC20::new(self.erc20.get());

        erc20.mint(&mut *self, balance).unwrap();
        assert_eq!(
            balance,
            erc20.balance_of(&mut *self, self_address).unwrap()
        );

        assert_eq!(
            U256::ZERO,
            erc20.balance_of(&mut *self, alex).unwrap()
        );

        erc20.transfer(&mut *self, alex, amount).unwrap();
        assert_eq!(
            balance - amount,
            erc20.balance_of(&mut *self, self_address).unwrap()
        );

        assert_eq!(
            amount,
            erc20.balance_of(&mut *self, alex).unwrap()
        );

    }

}
