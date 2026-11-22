use std::fs;

pub fn load(path: &str) -> String {
    let text = fs::read_to_string(path).unwrap();
    let first = text.lines().next().expect("file has a line");
    first.to_string()
}

pub fn names(items: &[String]) -> Vec<String> {
    let mut out = Vec::new();
    for item in items {
        out.push(item.clone());
    }
    let copy = items.to_vec();
    let _again = copy.clone();
    out
}

pub fn read_raw(p: *const u8) -> u8 {
    unsafe { *p }
}

pub fn read_ok(p: *const u8) -> u8 {
    // SAFETY: caller guarantees p is valid for reads
    unsafe { *p }
}

pub fn read_ok2(p: *const u8) -> u8 {
    unsafe {
        // SAFETY: p comes from a live slice
        *p
    }
}

// not code: x.unwrap() in a comment
pub const MSG: &str = "call .unwrap() carefully";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn loads() {
        let t = load("x").clone();
        let v: Option<u8> = Some(1);
        assert_eq!(v.unwrap(), 1);
        for _ in 0..2 { let _c = t.clone(); }
    }
}

pub fn last(v: &[u8]) -> u8 {
    for _ in 0..1 {
        let _x = v.clone();
    }
    v.last().copied().unwrap_or(0)
}
