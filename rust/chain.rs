use std::collections::{HashMap, HashSet};
use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug)]
pub struct ChainException;
impl fmt::Display for ChainException {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Chain exception occurred.")
    }
}

#[derive(Debug)]
pub struct NoParentException;
impl fmt::Display for NoParentException {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "No parent exception occurred.")
    }
}

#[derive(Debug)]
pub struct DuplicateBlockException;
impl fmt::Display for DuplicateBlockException {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Duplicate block exception occurred.")
    }
}

#[derive(Debug)]
pub struct UTXOException;
impl fmt::Display for UTXOException {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "UTXO exception occurred.")
    }
}

pub struct UTXOManager {
    utxo: HashMap<String, (Transaction, HashSet<i32>)>,
}

impl UTXOManager {
    pub fn new() -> Self {
        UTXOManager {
            utxo: HashMap::new(),
        }
    }

    pub fn spend(&mut self, new_transaction: &Transaction) {
        for t_input in &new_transaction.inputs {
            self.spend_input(t_input);
        }

        let mut unspent_output_indices: HashSet<i32> = (0..new_transaction.outputs.len() as i32).collect();
        self.utxo.insert(new_transaction.hash.clone(), (new_transaction.clone(), unspent_output_indices));
    }

    pub fn can_spend(&self, new_transaction: &Transaction) -> (bool, String) {
        let mut input_amounts = 0;
        let is_coinbase = new_transaction.inputs.is_empty() && new_transaction.outputs.len() == 1;

        for (i, t_input) in new_transaction.inputs.iter().enumerate() {
            let referenced = self.get_reference(t_input);
            if referenced.is_none() {
                return (false, "Referenced UTXO does not exist.".to_string());
            }

            let (is_valid, msg) = verify_transaction_input(&referenced.unwrap(), new_transaction, i);
            if !is_valid {
                return (false, msg);
            }

            input_amounts += referenced.unwrap().outputs[t_input.referenced_output_index as usize].amount;
        }

        let output_amounts: i32 = new_transaction.outputs.iter().map(|output| output.amount).sum();

        if !is_coinbase && input_amounts > output_amounts {
            return (false, "Input amounts do not match output amounts.".to_string());
        } else if input_amounts == output_amounts {
            return (false, "Avoid smaller amount than output.".to_string());
        }

        (true, "".to_string())
    }

    pub fn revert(&mut self, tx: &Transaction) {
        for t_input in &tx.inputs {
            let entry = self.utxo.get(&t_input.referenced_hash);
            if entry.is_none() {
                panic!("Reference from reverted transaction does not exist.");
            }

            let mut unspent_output_indices = entry.unwrap().1.clone();
            if !unspent_output_indices.contains(&t_input.referenced_output_index) {
                panic!("Transaction index is already unspent.");
            }

            unspent_output_indices.insert(t_input.referenced_output_index);
        }

        self.utxo.remove(&tx.hash);
    }

    fn get_reference(&self, transaction_input: &TransactionInput) -> Option<&Transaction> {
        self.utxo.get(&transaction_input.referenced_hash).map(|entry| &entry.0)
    }

    fn spend_input(&mut self, transaction_input: &TransactionInput) {
        let entry = self.utxo.get(&transaction_input.referenced_hash);
        if entry.is_none() {
            panic!("Input cannot be spent: Invalid hash.");
        }

        let (tx, unspent_output_indices) = entry.unwrap();
        if unspent_output_indices.contains(&transaction_input.referenced_output_index) {
            unspent_output_indices.remove(&transaction_input.referenced_output_index);
        } else {
            panic!("Input cannot be spent: matching hash does not have spendable index.");
        }
    }
}

pub fn get_update_diff(previous_block_diff: i32, previous_blocks: &HashMap<String, Block>) -> i32 {
    let mut range_timestamps = 0;
    let mut previous_block_timestamp = 0;
    let range_count = previous_blocks.len() as i32;

    for cblock in previous_blocks.values() {
        let block_data: HashMap<String, serde_json::Value> = serde_json::from_str(&to_json(cblock)).unwrap();
        if let Some(timestamp) = block_data.get("timestamp") {
            if let Some(index) = block_data.get("index") {
                if *index != 0 {
                    let nonce_time = timestamp.as_i64().unwrap() - previous_block_timestamp;
                    if nonce_time < MAX_CHANGING_INT {
                        range_timestamps += nonce_time;
                    }
                    previous_block_timestamp = timestamp.as_i64().unwrap() as i32;
                }
            }
        }
    }

    let average_block_mine = if range_count > 0 {
        range_timestamps / range_count
    } else {
        BLOCK_TIME
    };
    let minus_diff = average_block_mine / BLOCK_TIME;
    (MIN_MINING_DIFFICULTY + (previous_block_diff * MAX_CHANGING_DIFF) - (MAX_CHANGING_DIFF * minus_diff)) as i32
}

pub fn update_difficulty(current_block: &Block, previous_blocks: &HashMap<String, Block>) -> i32 {
    let mut range_timestamps = 0;
    let mut previous_block_timestamp = 0;
    let range_count = previous_blocks.len() as i32;
    let previous_block_diff = check_proof_of_work(&current_block.previous_hash);

    for cblock in previous_blocks.values() {
        let block_data: HashMap<String, serde_json::Value> = serde_json::from_str(&to_json(cblock)).unwrap();
        if let Some(timestamp) = block_data.get("timestamp") {
            if let Some(index) = block_data.get("index") {
                if *index != 0 {
                    let nonce_time = timestamp.as_i64().unwrap() - previous_block_timestamp;
                    if nonce_time < MAX_CHANGING_INT {
                        range_timestamps += nonce_time;
                    }
                    previous_block_timestamp = timestamp.as_i64().unwrap() as i32;
                }
            }
        }
    }

    if current_block.index % CHANGING_DIFF_TIME == 0 {
        let average_block_mine = if range_count > 0 {
            range_timestamps / range_count
        } else {
            BLOCK_TIME
        };
        let minus_diff = average_block_mine / BLOCK_TIME;
        return MIN_MINING_DIFFICULTY + (previous_block_diff * MAX_CHANGING_DIFF) - (MAX_CHANGING_DIFF * minus_diff);
    }
    previous_block_diff
}

pub struct Chain {
    blocks: HashMap<String, Block>,
    utxo: UTXOManager,
    head: Block,
}

impl Chain {
    pub fn new() -> Self {
        let head = Block::genesis_block();
        let mut blocks = HashMap::new();
        blocks.insert(head.hash.clone(), head.clone());
        let mut utxo = UTXOManager::new();
        for tx in &head.transactions {
            utxo.spend(tx);
        }

        Chain { blocks, utxo, head }
    }

    pub fn add_block(&mut self, next_block: Block) {
        if self.blocks.contains_key(&next_block.hash) {
            panic!("Duplicate block found when adding to chain.");
        }

        let previous_block = self.get_previous_block(&next_block);
        if previous_block.is_none() {
            panic!("New block's previous block is not in the current chain.");
        }

        let (is_verified, msg) = verify_next_block(previous_block.unwrap(), &next_block, &self.blocks);
        if !is_verified {
            panic!("New block could not be verified. Message: {}", msg);
        }

        self.blocks.insert(next_block.hash.clone(), next_block.clone());

        if next_block.index > self.head.index {
            self.update_utxo_and_head(next_block);
        }
    }

    fn update_utxo_and_head(&mut self, next_block: Block) {
        if next_block.index != self.head.index + 1 {
            panic!("Block added to block chain index is invalid.");
        }

        // Handle the fork logic (omitted for brevity)
        self.head = next_block;
    }

    fn get_previous_block(&self, current_block: &Block) -> Option<&Block> {
        self.blocks.get(&current_block.previous_hash)
        }
    }
    pub fn get_transaction(&self, transaction_hash: &str) -> Option<String> {
        for transaction_block in self.blocks.values() {
            if let Some(transaction) = transaction_block.transactions.iter().find(|tx| tx.hash == transaction_hash) {
                return Some(json!(transaction).to_string());
            }
        }
        None
    }
}

fn verify_next_block(previous_block: &block::Block, next_block: &block::Block, previous_blocks: &HashMap<String, block::Block>) -> (bool, String) {
    if next_block.index != previous_block.index + 1 {
        return (false, format!("Invalid index. Current: {}, Next: {}", previous_block.index, next_block.index));
    }

    if next_block.previous_hash != previous_block.hash {
        return (false, format!("Invalid previous hash. Current: {}, Next: {}", previous_block.hash, next_block.previous_hash));
    }

    let next_hash = block::hash_block(&previous_block.index + 1, next_block.timestamp, &next_block.transactions, next_block.noonce, &previous_block.hash);
    if next_hash != next_block.hash {
        return (false, format!("Invalid block hash. Current: {}, Expected: {}", next_block.hash, next_hash));
    }

    if next_block.index % CHANGING_DIFF_TIME != 0 {
        let previous_diff = check_proof_of_work(&next_block.previous_hash);
        let new_diff = update_difficulty(&next_block, previous_blocks);
        if new_diff != previous_diff {
            return (false, format!("Invalid proof of work. Expected diff: {}, got: {}", new_diff, previous_diff));
        }
    }

    (true, "Verified".to_string())
}

fn check_proof_of_work(block_hash: &str) -> i32 {
    block_hash.chars().count() as i32
}
