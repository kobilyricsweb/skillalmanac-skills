import XCTest

final class FeedTests: XCTestCase {
    func testLoad() throws {
        let a = try! JSONSerialization.data(withJSONObject: [])
        let b = String(data: a, encoding: .utf8)!
        let c = [1][0] as! Int
        let d = Optional(1)!
        print(b, c, d)
    }
}
