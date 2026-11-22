use std::slice;

pub struct Buf {
    ptr: *mut u8,
    len: usize,
}

unsafe impl Send for Buf {}

impl Buf {
    pub fn as_slice(&self) -> &[u8] {
        unsafe { slice::from_raw_parts(self.ptr, self.len) }
    }

    pub fn checksum(&self) -> u32 {
        let mut sum = 0u32;
        for b in self.as_slice() {
            sum = sum.wrapping_add(*b as u32);
        }
        sum
    }

    pub fn names(&self, all: &[String]) -> Vec<String> {
        let mut out = Vec::new();
        for n in all {
            out.push(n.clone());
        }
        out
    }
}
