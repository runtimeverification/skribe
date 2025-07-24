// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

interface ICounter {
    function number() external view returns (uint256);
    function setNumber(uint256 newNumber) external;
    function increment() external;
}

contract CallCounter {
    function number(address counterAddr) public view returns (uint256) {
        return ICounter(counterAddr).number();
    }

    function setNumber(address counterAddr, uint256 newNumber) public {
        ICounter(counterAddr).setNumber(newNumber);
    }

    function increment(address counterAddr) public {
        ICounter(counterAddr).increment();
    }
}