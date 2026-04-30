// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ElectionResult
 * @dev Stores election result hashes for tamper-proof verification.
 * Part of the Hybrid E-Voting System FYP.
 */
contract ElectionResult {
    
    // Mapping from election ID to result hash
    mapping(string => string) private resultHashes;
    
    // Mapping to track which elections have been finalized
    mapping(string => bool) private isFinalized;
    
    // Event emitted when a result is stored
    event ResultStored(string electionId, string resultHash, uint256 timestamp);
    
    // Address of the contract owner (admin)
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only the owner can perform this action");
        _;
    }
    
    /**
     * @dev Store the result hash for an election
     * @param electionId Unique identifier of the election
     * @param resultHash SHA-256 hash of the election results
     */
    function storeResult(string memory electionId, string memory resultHash) public onlyOwner {
        require(!isFinalized[electionId], "Election results already finalized on blockchain");
        require(bytes(resultHash).length > 0, "Result hash cannot be empty");
        
        resultHashes[electionId] = resultHash;
        isFinalized[electionId] = true;
        
        emit ResultStored(electionId, resultHash, block.timestamp);
    }
    
    /**
     * @dev Get the stored result hash for an election
     * @param electionId Unique identifier of the election
     * @return The stored result hash
     */
    function getResult(string memory electionId) public view returns (string memory) {
        require(isFinalized[electionId], "Election not finalized on blockchain");
        return resultHashes[electionId];
    }
    
    /**
     * @dev Verify if a given hash matches the stored hash
     * @param electionId Unique identifier of the election
     * @param hashToVerify Hash to compare against stored hash
     * @return Whether the hashes match
     */
    function verifyResult(string memory electionId, string memory hashToVerify) public view returns (bool) {
        if (!isFinalized[electionId]) return false;
        return keccak256(abi.encodePacked(resultHashes[electionId])) == keccak256(abi.encodePacked(hashToVerify));
    }
    
    /**
     * @dev Check if an election has been finalized
     * @param electionId Unique identifier of the election
     * @return Whether the election is finalized
     */
    function isElectionFinalized(string memory electionId) public view returns (bool) {
        return isFinalized[electionId];
    }
}
