pragma solidity ^0.4.0;

contract LegacyContract {
    address public owner;
    uint256 public balance;
    bool public paused;
    
    // 0.4.x风格构造函数
    function LegacyContract() public {
        owner = msg.sender;
        balance = 0;
        paused = false;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }
    
    modifier whenNotPaused() {
        require(!paused);
        _;
    }
    
    function deposit() public payable whenNotPaused {
        balance += msg.value;
    }
    
    function withdraw(uint256 amount) public onlyOwner whenNotPaused {
        require(amount <= balance);
        balance -= amount;
        msg.sender.transfer(amount);
    }
    
    function pause() public onlyOwner {
        paused = true;
    }
    
    function unpause() public onlyOwner {
        paused = false;
    }
    
    function getBalance() public constant returns (uint256) {
        return balance;
    }
    
    function isPaused() public constant returns (bool) {
        return paused;
    }
    
    // 使用0.4.x的now关键字
    function getTime() public constant returns (uint256) {
        return now;
    }
    
    // 使用suicide（已弃用）
    function destroy() public onlyOwner {
        suicide(owner);
    }
}