use std::collections::HashMap;
use std::fs;

pub struct Config {
    pub values: HashMap<String, String>,
}

pub fn load(path: &str) -> Config {
    let text = fs::read_to_string(path).unwrap();
    let mut values = HashMap::new();
    for line in text.lines() {
        let (k, v) = line.split_once('=').expect("line without =");
        values.insert(k.trim().to_string(), v.trim().to_string());
    }
    Config { values }
}

pub fn get_port(cfg: &Config) -> u16 {
    cfg.values.get("port").unwrap().parse().unwrap()
}
