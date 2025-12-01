use stylus_sdk::alloy_primitives::{address, Address};
use stylus_sdk::prelude::*;

sol_interface! {

interface ICheatcodes {

    /// Signs `digest` with `privateKey` using the secp256k1 curve.
    function sign(uint256 private_key, bytes32 digest) external pure returns (uint8 v, bytes32 r, bytes32 s);

    /// Gets the address for a given private key.
    function addr(uint256 private_key) external pure returns (address keyAddr);

    /// Gets the nonce of an account.
    function getNonce(address account) external view returns (uint64 nonce);

    /// Loads a storage slot from an address.
    function load(address target, bytes32 slot) external view returns (bytes32 data);

    /// Get the path of the current project root.
    function projectRoot() external view returns (string memory path);

    // Reads the entire content of file to string, (path) => (data)
    function readFile(string calldata) external returns (string memory);

    /// Reads the entire content of file as binary. `path` is relative to the project root.
    function readFileBinary(string calldata path) external view returns (bytes memory data);

    /// Asserts that the given condition is true.
    function assertTrue(bool condition) external pure;

    /// If the condition is false, discard this run's fuzz inputs and generate new ones.
    function assume(bool condition) external pure;

    /// Sets an address' balance.
    function deal(address account, uint256 new_balance) external;

    /// Sets an address' code.
    function etch(address target, bytes calldata new_runtime_bytecode) external;

    /// Sets `block.basefee`.
    function fee(uint256 new_basefee) external;

    /// Sets the *next* call's `msg.sender` to be the input address.
    function prank(address msg_sender) external;

    /// Sets all subsequent calls' `msg.sender` to be the input address until `stopPrank` is called.
    function startPrank(address msg_sender) external;

    /// Resets subsequent calls' `msg.sender` to be `address(this)`.
    function stopPrank() external;

    /// Stores a value to an address' storage slot.
    function store(address target, bytes32 slot, bytes32 value) external;

    /// Sets `block.timestamp`.
    function warp(uint256 new_timestamp) external;

    /// Prepare an expected log with all topic and data checks enabled.
    /// Call this function, then emit an event, then call a function. Internally after the call, we check if
    /// logs were emitted in the expected order with the expected topics and data.
    function expectEmit() external;

    /// Expects an error on next call with any revert data.
    function expectRevert() external;

}

}

pub const CHEATCODE_ADDRESS: Address = address!("0x7109709ECFA91A80626FF3989D68F67F5B1DD12D");

pub fn cheat() -> ICheatcodes {
    ICheatcodes::new(CHEATCODE_ADDRESS)
}

pub fn build_init_code(bytecode: &[u8]) -> Vec<u8> {
    // length(prefix + bytecode)
    let length: u32 = (bytecode.len() + 4) as u32;
    let bs_length: [u8; 4] = length.to_be_bytes();

    let mut init_code = Vec::new();

    // PUSH4 <length(bytecode)>
    init_code.push(0x63);
    init_code.extend_from_slice(&bs_length);

    // DUP1
    init_code.push(0x80);

    // PUSH1 <length(prelude + version)>
    init_code.push(0x60);
    init_code.push((14 + 1) as u8);

    // PUSH1 0x00
    init_code.push(0x60);
    init_code.push(0x00);

    // CODECOPY
    init_code.push(0x39);

    // PUSH1 0x00
    init_code.push(0x60);
    init_code.push(0x00);

    // RETURN
    init_code.push(0xf3);

    // version
    init_code.push(0x00);

    // Stylus discriminant + compression level
    init_code.extend_from_slice(&[0xef, 0xf0, 0x00, 0x00]);

    // Append actual bytecode
    init_code.extend_from_slice(bytecode);

    init_code
}
