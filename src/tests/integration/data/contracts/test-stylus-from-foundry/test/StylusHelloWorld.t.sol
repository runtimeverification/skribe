// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Test} from "forge-std/Test.sol";

interface ICounter {
    function number() external view returns (uint256);
    function setNumber(uint256 newNumber) external;
    function increment() external;
}

contract TestStylusHelloWorld is Test {

    ICounter counter;

    function setUp() public {
        bytes memory bytecode = vm.readFileBinary("wasm/stylus_hello_world.wasm");
        bytes memory initCode = abi.encodePacked(
            hex"7f",              // PUSH32
            bytecode.length + 4,  // length(prefix + bytecode)
            hex"80",              // DUP1
            hex"60",              // PUSH1
            bytes1(uint8(42 + 1)),    // prelude + version
            hex"60",        // PUSH1
            hex"00",
            hex"39",        // CODECOPY
            hex"60",        // PUSH1
            hex"00",
            hex"f3",        // RETURN
            hex"00",        // version
            hex"eff000",    // Stylus discriminant
            hex"00",        // compression (?) level
            bytecode
        );

        address newContractAddress;
        assembly {
            newContractAddress := create(0, add(initCode, 0x20), mload(initCode))
        }

        counter = ICounter(newContractAddress);
    }

    function test_SetAndIncrement(uint256 x) public {
        vm.assume( x < UINT256_MAX );

        counter.setNumber(x);
        counter.increment();

        assertEq(counter.number(), x + 1);
    }

}
