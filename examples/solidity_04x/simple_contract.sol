pragma solidity 0.4.24;

contract SimpleStorage {
    uint256 public storedData;
    
    function SimpleStorage(uint256 initialValue) public {
        storedData = initialValue;
    }
    
    function set(uint256 data) public {
        storedData = data;
    }
    
    function get() public constant returns (uint256) {
        return storedData;
    }
}