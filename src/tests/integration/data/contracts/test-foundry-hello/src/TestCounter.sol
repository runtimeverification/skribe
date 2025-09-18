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

    function subtractFromTestNumber(uint256 x) public {
        testNumber -= x;
    }

    function test_NumberIs42() public {
        assertEq(testNumber, 42);
    }
 
    function testRevert_Subtract43() public {
        vm.expectRevert();
        this.subtractFromTestNumber(43);
    }

    function test_Subtract(uint256 x) public {
        if( x > 42 ) {
            vm.expectRevert();
        }
        this.subtractFromTestNumber(x);
    }

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