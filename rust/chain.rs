use std::collections::{HashMap, HashSet};
use serde_json::json;
use std::error::Error;

#[derive(Debug)]
pub struct ChainException(String);

impl std::fmt::Display for ChainException {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "ChainException: {}", self.0)
    }
}

impl Error for ChainException {}

#[derive(Debug)]
pub struct NoParentException;

impl std::fmt::Display for NoParentException {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "NoParentException")
    }
}

impl Error for NoParentException {}

#[derive(Debug)]
pub struct DuplicateBlockException;

impl std::fmt::Display for DuplicateBlockException {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "DuplicateBlockException")
    }
}

impl Error for DuplicateBlockException {}

#[derive(Debug)]
pub struct UTXOException;

impl std::fmt::Display for UTXOException {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "UTXOException")
    }
}

impl Error for UTXOException {}

pub struct UTXOManager {
    utxo: HashMap<String, (transaction::Transaction, HashSet<usize>)>,
}

impl UTXOManager {
    pub fn new() -> Self {
        UTXOManager {
            utxo: HashMap::new(),
        }
    }

    pub fn spend(&mut self, new_transaction: &transaction::Transaction) {
        for input in &new_transaction.inputs {
            self.spend_input(input);
        }

        let unspent_output_indices: HashSet<usize> = (0..new_transaction.outputs.len()).collect();
        self.utxo.insert(new_transaction.hash.clone(), (new_transaction.clone(), unspent_output_indices));
    }

    pub fn can_spend(&self, new_transaction: &transaction::Transaction) -> Result<bool, String> {
        let mut input_amounts = 0;
        let is_coinbase = new_transaction.inputs.is_empty() && new_transaction.outputs.len() == 1;

        for (i, t_input) in new_transaction.inputs.iter().enumerate() {
            if let Some(referenced) = self.get_reference(t_input) {
                let (is_valid, msg) = transaction::verify_transaction_input(&referenced, new_transaction, i);
                if !is_valid {
                    return Err(msg);
                }

                input_amounts += referenced.outputs[t_input.referenced_output_index].amount;
            } else {
                return Err("Referenced UTXO does not exist.".to_string());
            }
        }

        let output_amounts: usize = new_transaction.outputs.iter().map(|output| output.amount).sum();

        if !is_coinbase && input_amounts > output_amounts {
            return Err("Input amounts do not match output amounts.".to_string());
        } else if input_amounts == output_amounts {
            return Err("Avoid smaller amount than output.".to_string());
        }

        Ok(true)
    }

    pub fn revert(&mut self, tx: &transaction::Transaction) {
        for input in &tx.inputs {
            if let Some(entry) = self.utxo.get(&input.referenced_hash) {
                let mut unspent_output_indices = entry.1.clone();
                if !unspent_output_indices.insert(input.referenced_output_index) {
                    panic!("Transaction index is already unspent.");
                }
            } else {
                panic!("Reference from reverted transaction does not exist.");
            }
        }

        self.utxo.remove(&tx.hash);
    }

    fn get_reference(&self, transaction_input: &transaction::TransactionInput) -> Option<transaction::Transaction> {
        self.utxo.get(&transaction_input.referenced_hash).map(|entry| entry.0.clone())
    }

    fn spend_input(&mut self, transaction_input: &transaction::TransactionInput) {
        if let Some(entry) = self.utxo.get_mut(&transaction_input.referenced_hash) {
            let unspent_output_indices = &mut entry.1;
            if !unspent_output_indices.remove(&transaction_input.referenced_output_index) {
                panic!("Input cannot be spent: matching hash does not have spendable index.");
            }
        } else {
            panic!("Input cannot be spent: Invalid hash.");
        }
    }
}

pub fn get_update_diff(previous_block_diff: i32, previous_blocks: &HashMap<String, block::Block>) -> i32 {
    let mut range_timestamps = 0;
    let mut previous_block_timestamp = 0;
    let range_count = previous_blocks.len() as i32;

    for cblock in previous_blocks.values() {
        let block_data = json::parse(&block::to_json(cblock)).unwrap();
        if let Some(timestamp) = block_data["timestamp"].as_i64() {
            if block_data["index"].as_i64().unwrap_or(0) != 0 {
                let nonce_time = timestamp as i32 - previous_block_timestamp;
                if nonce_time < MAX_CHANGING_INT {
                    range_timestamps += nonce_time;
                }
                previous_block_timestamp = timestamp as i32;
            }
        }
    }

    let average_block_mine = if range_count != 0 { range_timestamps / range_count } else { BLOCK_TIME };
    let minus_diff = average_block_mine as f32 / BLOCK_TIME as f32;
    (MIN_MINING_DIFFICULTY + (previous_block_diff * MAX_CHANGING_DIFF) - (MAX_CHANGING_DIFF * minus_diff as i32)) as i32
}

pub fn update_difficulty(current_block: &block::Block, previous_blocks: &HashMap<String, block::Block>) -> i32 {
    let mut range_timestamps = 0;
    let mut previous_block_timestamp = 0;
    let range_count = previous_blocks.len() as i32;
    let previous_block_diff = check_proof_of_work(&current_block.previous_hash);

    for cblock in previous_blocks.values() {
        let block_data = json::parse(&block::to_json(cblock)).unwrap();
        if let Some(timestamp) = block_data["timestamp"].as_i64() {
            if block_data["index"].as_i64().unwrap_or(0) != 0 {
                let nonce_time = timestamp as i32 - previous_block_timestamp;
                if nonce_time < MAX_CHANGING_INT {
                    range_timestamps += nonce_time;
                }
                previous_block_timestamp = timestamp as i32;
            }
        }
    }

    if current_block.index % CHANGING_DIFF_TIME == 0 {
        let average_block_mine = if range_count != 0 { range_timestamps / range_count } else { BLOCK_TIME };
        let minus_diff = average_block_mine as f32 / BLOCK_TIME as f32;
        (MIN_MINING_DIFFICULTY + (previous_block_diff * MAX_CHANGING_DIFF) - (MAX_CHANGING_DIFF * minus_diff as i32)) as i32
    } else {
        previous_block_diff
    }
}

pub struct Chain {
    blocks: HashMap<String, block::Block>,
    utxo: UTXOManager,
    head: block::Block,
}

impl Chain {
    pub fn new() -> Self {
        let head = block::genesis_block();
        let mut blocks = HashMap::new();
        blocks.insert(head.hash.clone(), head.clone());
        let mut utxo = UTXOManager::new();
        for tx in &head.transactions {
            utxo.spend(tx);
        }

        Chain { blocks, utxo, head }
    }

    pub fn add_block(&mut self, next_block: block::Block) -> Result<(), ChainException> {
        if self.blocks.contains_key(&next_block.hash) {
            return Err(ChainException("Duplicate block found when adding to chain.".to_string()));
        }

        let previous_block = self.get_previous_block(&next_block).ok_or(NoParentException)?;

        let (is_verified, msg) = verify_next_block(&previous_block, &next_block, &self.blocks);
        if !is_verified {
            return Err(ChainException(format!("New block could not be verified. Message: {}", msg)));
        }

        self.blocks.insert(next_block.hash.clone(), next_block.clone());

        if next_block.index > self.head.index {
            self.update_utxo_and_head(next_block);
        }

        Ok(())
    }

    fn update_utxo_and_head(&mut self, next_block: block::Block) {
        if next_block.index != self.head.index + 1 {
            panic!("Block added to block chain index is invalid");
        }

        let mut old_chain = Vec::new();
        let mut new_chain = vec![next_block];

        let mut old_parent = self.head.clone();
        let mut new_parent = self.get_previous_block(&next_block).unwrap();

        while old_parent.hash != new_parent.hash {
            for tx in old_parent.transactions.iter().rev() {
                self.utxo.revert(tx);
            }

            old_chain.push(old_parent.clone());
            new_chain.push(new_parent.clone());

            old_parent = self.get_previous_block(&old_parent).unwrap();
            new_parent = self.get_previous_block(&new_parent).unwrap();
        }

        for i in (0..new_chain.len()).rev() {
            for tx in &new_chain[i].transactions {
                if let Ok(true) = self.utxo.can_spend(tx) {
                    self.utxo.spend(tx);
                } else {
                    for tx_index in (0..i).rev() {
                        self.utxo.revert(&new_chain[tx_index].transactions[tx_index]);
                    }
                    for block_index in (i + 1..new_chain.len()).rev() {
                        for tx in &new_chain[block_index].transactions {
                            self.utxo.revert(tx);
                        }
                    }
                    for block in old_chain.iter().rev() {
                        for tx in &block.transactions {
                            self.utxo.spend(tx);
                        }
                    }

                    panic!("Invalid transaction found.");
                }
            }
        }

        self.head = next_block;
    }

    fn get_previous_block(&self, current_block: &block::Block) -> Option<&block::Block> {
        self.blocks.get(&current_block.previous_hash)
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
