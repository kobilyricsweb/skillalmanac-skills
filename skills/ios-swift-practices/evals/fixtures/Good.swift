import SwiftUI
import os

@Observable
final class ProfileModel {
    var name = ""
    var isLoading = false
}

struct ProfileView: View {
    @State private var model = ProfileModel()
    @State private var draft = ""
    @Binding var isPresented: Bool
    private let log = Logger(subsystem: "app", category: "profile")

    var body: some View {
        VStack {
            if !draft.isEmpty, draft != "x" {
                Text(draft)
            }
            Button("Close") { isPresented = false }
        }
        .task { await load() }
    }

    @MainActor
    func load() async {
        model.isLoading = true
        let value = try? await fetch()
        guard let value else { return }
        model.name = value
        log.info("loaded")
    }

    func fetch() async throws -> String { "x" }
}
