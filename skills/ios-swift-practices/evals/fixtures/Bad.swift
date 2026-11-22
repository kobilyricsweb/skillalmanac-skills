import SwiftUI
import Foundation

final class Counter {
    var count = 0
}

class FeedModel: ObservableObject {
    @Published var items: [String] = []
}

@Observable
final class GoodModel {
    var title = ""
}

struct FeedView: View {
    @State private var counter = Counter()
    @State private var feed = FeedModel()
    @State private var good = GoodModel()
    @State private var query = ""
    @State private var service: SyncService?

    var body: some View {
        Text("Items: \(feed.items.count)")
    }

    func load() async {
        let data = try! Data(contentsOf: URL(string: "https://example.com/a")!)
        let name = String(data: data, encoding: .utf8)!
        print("loaded \(name)")
        DispatchQueue.main.async {
            self.query = name
        }
        Task {
            DispatchQueue.main.async { self.query = "x" }
        }
    }

    func plain() {
        DispatchQueue.main.async { self.query = "ok" }
        #if DEBUG
        print("debug only")
        #endif
        let s = "a ! b // not code print(x) try! y!"
        // print("comment") try! z!
        let v = items[0] as! String
    }
}
