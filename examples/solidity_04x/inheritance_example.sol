pragma solidity 0.4.25;

contract BaseContract {
    uint256 public baseValue;
    address public owner;
    
    function BaseContract() public {
        owner = msg.sender;
        baseValue = 100;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }
    
    function setBaseValue(uint256 _value) public onlyOwner {
        baseValue = _value;
    }
    
    function getBaseValue() public constant returns (uint256) {
        return baseValue;
    }
}

contract ChildContract is BaseContract {
    uint256 public childValue;
    string public name;
    
    function ChildContract(uint256 _initialValue, string _name) public {
        childValue = _initialValue;
        name = _name;
    }
    
    function setChildValue(uint256 _value) public {
        childValue = _value;
    }
    
    function getChildValue() public constant returns (uint256) {
        return childValue;
    }
    
    function getTotalValue() public constant returns (uint256) {
        return baseValue + childValue;
    }
    
    function getName() public constant returns (string) {
        return name;
    }
}

contract GrandChildContract is ChildContract {
    uint256 public grandChildValue;
    
    function GrandChildContract(uint256 _grandValue) public {
        grandChildValue = _grandValue;
    }
    
    function setGrandChildValue(uint256 _value) public onlyOwner {
        grandChildValue = _value;
    }
    
    function getGrandChildValue() public constant returns (uint256) {
        return grandChildValue;
    }
    
    function getAllValues() public constant returns (uint256, uint256, uint256) {
        return (baseValue, childValue, grandChildValue);
    }
}