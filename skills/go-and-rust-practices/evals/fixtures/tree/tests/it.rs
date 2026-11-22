fn t() { let _ = Some(1).unwrap(); unsafe { core::ptr::null::<u8>().read() }; }
