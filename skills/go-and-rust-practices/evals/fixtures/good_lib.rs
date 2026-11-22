use std::fmt;

#[derive(Debug)]
pub enum LoadError {
    Missing(String),
}

impl fmt::Display for LoadError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LoadError::Missing(p) => write!(f, "missing {p}"),
        }
    }
}

impl std::error::Error for LoadError {}

pub fn load(path: &str) -> Result<String, LoadError> {
    std::fs::read_to_string(path).map_err(|_| LoadError::Missing(path.to_string()))
}

pub fn apply<F>(f: F) -> String
where
    F: for<'a> Fn(&'a str) -> &'a str,
{
    f("x").to_string().clone()
}

pub struct Raw(*mut u8);

// SAFETY: Raw is only created from a pointer the owner never aliases.
unsafe impl Send for Raw {}

pub fn first(v: &[u8]) -> Option<u8> {
    // SAFETY: the slice is checked non-empty on the next line
    if v.is_empty() { None } else { Some(unsafe { *v.get_unchecked(0) }) }
}

pub fn pick(v: &[u8]) -> u8 {
    let cfg = v.first().copied().unwrap(); // gorust:ignore
    cfg
}
