use chrono::prelude::*;
use serde::{Serialize, Deserialize};
use std::collections::HashMap;

// Transaction Struct (simplified)
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Transaction {
    pub timestamp: f64,
    pub output_addresses: Vec<String>,
    pub output_amounts: Vec<u64>,
}

impl Transaction {
    pub fn new(timestamp: f64, output_addresses: Vec<String>, output_amounts: Vec<u64>) -> Self {
        Transaction { timestamp, output_addresses, output_amounts }
    }
}

// Block Struct
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct Block {
    pub index: usize,
    pub timestamp: f64,
    pub transactions: Vec<Transaction>,
    pub noonce: usize,
    pub previous_hash: String,
    pub hash: String,
    pub parent_blocks: Vec<String>, // for DAG structure
}

impl Block {
    // Calculate block hash (same as in Python, but using Rust's SHA256 library)
    pub fn hash_block(&self) -> String {
        let combined_transactions: String = self.transactions.iter()
            .map(|tx| format!("{:?}", tx)) // Stringify transactions
            .collect();
        
        let block_data = format!(
            "{}{}{}{}{}{}",
            self.index,
            self.timestamp,
            combined_transactions,
            self.noonce,
            self.previous_hash,
            self.parent_blocks.join(",")
        );

        // Use Rust's SHA256 to hash the block data
        use sha2::{Sha256, Digest};
        let mut hasher = Sha256::new();
        hasher.update(block_data.as_bytes());
        let result = hasher.finalize();
        hex::encode(result)
    }

    // Create a new Block (with or without parent blocks)
    pub fn new(index: usize, timestamp: f64, transactions: Vec<Transaction>, noonce: usize, previous_hash: String, parent_blocks: Vec<String>) -> Self {
        let block = Block {
            index,
            timestamp,
            transactions,
            noonce,
            previous_hash,
            parent_blocks,
            hash: String::new(), // Initially empty, will be computed
        };
        let hash = block.hash_block();
        Block { hash, ..block }
    }

    // To JSON (using Serde for serialization)
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap()
    }

    // Create block from JSON (deserialization)
    pub fn from_json(json_str: &str) -> Block {
        serde_json::from_str(json_str).unwrap()
    }
}

// Genesis Block (first block in the chain)
pub fn genesis_block() -> Block {
    let genesis_time = 1725615747.2513995;
    let genesis_address = String::from("30820122300d06092a864886f70d01010105000382010f003082010a0282010100b0bb73e00ebdc83794c8b926253e6f72a45b8ef487ffe565941fcd74384884a95939fc0e1213db0dfbab83dcd3902af5b6c7391a453324b956aa5be8d58cf2d5b9e9667429ee40abe8a0d0ad831939454b61db63281f2d42665dccc0088f67291926dfdb321efd7b77ad5e571b16acc931aa31046423ba16ae5c1d3d613dcf2331041d90d0f39e0fd85f30238925d00198a765e0f6c721aa7372bc5cb648156dbaf98bfe16aab9eba12545e05253fb9aab932da75067dc432ac9228b42252c1fb4d5851a5108afa063c4b4f1d1795074e66a2c92261a3d976314134bbd3ba7ae0eb1938a936381239d6f6127b846fc42c99a9fcf36984a83a924ed0522ea24830203010001");
    
    let genesis_transaction = Transaction::new(genesis_time, vec![genesis_address], vec![100]);

    Block::new(
        0, 
        genesis_time, 
        vec![genesis_transaction],
        0, 
        String::from("AverCoin is a future, and i want to be in it."),
        vec![] // Genesis block has no parents
    )
}
