use std::fmt;
use std::time::{SystemTime, UNIX_EPOCH};
use serde::{Serialize, Deserialize};
use avercoin::blockchain::transaction::{Transaction, create_transaction, create_from_dictionary};
use sha2::{Sha256, Digest};

#[derive(Debug)]
pub struct BlockException;

impl fmt::Display for BlockException {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Block exception occurred")
    }
}

#[derive(Serialize, Deserialize, Clone)]
pub struct Block {
    pub index: usize,
    pub timestamp: f64,
    pub transactions: Vec<Transaction>,
    pub noonce: usize,
    pub previous_hash: String,
    pub hash: String,
}

impl Block {
    pub fn new(
        index: usize,
        timestamp: f64,
        transactions: Vec<Transaction>,
        noonce: usize,
        previous_hash: String,
    ) -> Self {
        let hash = hash_block(index, timestamp, &transactions, noonce, &previous_hash);
        Self {
            index,
            timestamp,
            transactions,
            noonce,
            previous_hash,
            hash,
        }
    }

    pub fn as_json(&self) -> String {
        serde_json::to_string_pretty(self).unwrap()
    }
}

impl PartialEq for Block {
    fn eq(&self, other: &Self) -> bool {
        let lhs = hash_block(
            self.index,
            self.timestamp,
            &self.transactions,
            self.noonce,
            &self.previous_hash,
        );
        let rhs = hash_block(
            other.index,
            other.timestamp,
            &other.transactions,
            other.noonce,
            &other.previous_hash,
        );
        lhs == rhs
    }
}

pub fn hash_block(
    index: usize,
    timestamp: f64,
    transactions: &[Transaction],
    noonce: usize,
    previous_hash: &str,
) -> String {
    let combined_transaction: String = transactions
        .iter()
        .map(|tx| tx.hash.clone())
        .collect::<Vec<String>>()
        .join("");

    let input = format!(
        "{}{}{}{}{}",
        index, timestamp, combined_transaction, noonce, previous_hash
    );

    let mut hasher = Sha256::new();
    hasher.update(input.as_bytes());
    let result = hasher.finalize();
    hex::encode(result)
}

pub fn genesis_block() -> Block {
    let genesis_time = 1725615747.2513995;
    let genesis_address = "30820122300d06092a864886f70d01010105000382010f003082010a0282010100b0bb73e00ebdc83794c8b926253e6f72a45b8ef487ffe565941fcd74384884a95939fc0e1213db0dfbab83dcd3902af5b6c7391a453324b956aa5be8d58cf2d5b9e9667429ee40abe8a0d0ad831939454b61db63281f2d42665dccc0088f67291926dfdb321efd7b77ad5e571b16acc931aa31046423ba16ae5c1d3d613dcf2331041d90d0f39e0fd85f30238925d00198a765e0f6c721aa7372bc5cb648156dbaf98bfe16aab9eba12545e05253fb9aab932da75067dc432ac9228b42252c1fb4d5851a5108afa063c4b4f1d1795074e66a2c92261a3d976314134bbd3ba7ae0eb1938a936381239d6f6127b846fc42c99a9fcf36984a83a924ed0522ea24830203010001";
    let genesis_transaction = create_transaction(
        vec![genesis_address.to_string()],
        vec![100],
        genesis_time,
    );

    Block::new(
        0,
        genesis_time,
        vec![genesis_transaction],
        0,
        "AverCoin is a future, and i want to be in it.".to_string(),
    )
}

pub fn to_json<T: Serialize>(value: &T) -> String {
    serde_json::to_string_pretty(value).unwrap()
}

pub fn create_from_json(json_block: &str) -> Result<Block, BlockException> {
    let deserialized: serde_json::Value = serde_json::from_str(json_block).unwrap();
    let transactions_json = deserialized["transactions"].as_array().unwrap();

    let transactions: Vec<Transaction> = transactions_json
        .iter()
        .map(|tx| create_from_dictionary(tx))
        .collect();

    let index = deserialized["index"].as_u64().unwrap() as usize;
    let timestamp = deserialized["timestamp"].as_f64().unwrap();
    let noonce = deserialized["noonce"].as_u64().unwrap() as usize;
    let previous_hash = deserialized["previousHash"].as_str().unwrap().to_string();
    let hash = deserialized["hash"].as_str().unwrap().to_string();

    let obj = Block::new(index, timestamp, transactions, noonce, previous_hash);

    if obj.hash != hash {
        Err(BlockException)
    } else {
        Ok(obj)
    }
}
