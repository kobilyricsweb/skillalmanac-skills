fn main() {
    let cfg = cfgtool::load("app.conf");
    println!("listening on {}", cfgtool::get_port(&cfg));
}
