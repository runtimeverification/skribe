// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Test} from "forge-std/Test.sol";

contract Counter {
    uint256 public number;

    function setNumber(uint256 newNumber) public {
        number = newNumber;
    }

    function increment() public {
        number++;
    }
}

contract CounterTest is Test {
    uint256 testNumber;
    Counter counter;

    function setUp() public {
        testNumber = 42;
        counter = new Counter();
    }
 
    function test_NumberIs42() public {
        assertEq(testNumber, 42);
    }
 
    /// forge-config: default.allow_internal_expect_revert = true
    /// TODO implement failing tests
    // function testRevert_Subtract43() public {
    //     vm.expectRevert();
    //     testNumber -= 43;
    // }

    function test_IncrementZero() public {
        assertEq(counter.number(), 0);
        counter.increment();
        assertEq(counter.number(), 1);
    }


    function test_SetAndIncrement(uint256 x) public {
        counter.setNumber(x);
        if( x < UINT256_MAX ) {
          counter.increment();
          assertEq(counter.number(), x + 1);
        }
    }

}