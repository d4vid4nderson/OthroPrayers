import SwiftUI

/// Edit mode for an office.
///
/// Nothing here touches the published text. The reader is arranging references
/// to prayers, and "Restore printed order" throws the arrangement away.
struct ArrangeView: View {
    let slug: String
    let title: String

    @EnvironmentObject private var library: Library
    @EnvironmentObject private var arrangements: Arrangements
    @Environment(\.dismiss) private var dismiss

    @State private var working: [ArrangedPrayer] = []
    @State private var showPalette = false
    @State private var loaded = false

    var body: some View {
        List {
            Section {
                ForEach(working) { prayer in
                    row(prayer)
                }
                .onMove { working.move(fromOffsets: $0, toOffset: $1) }
                .onDelete { working.remove(atOffsets: $0) }
            } header: {
                Text("In this office")
            } footer: {
                Text(working.isEmpty
                     ? "This office is empty. Add a prayer to begin."
                     : "Drag to reorder, swipe to remove. The printed office is kept and can be restored at any time.")
            }

            Section {
                Button { showPalette = true } label: {
                    Label("Add a prayer", systemImage: "plus.circle")
                }
                if arrangements.isCustomised(slug) {
                    Button(role: .destructive) {
                        arrangements.reset(slug)
                        dismiss()
                    } label: {
                        Label("Restore printed order", systemImage: "arrow.uturn.backward")
                    }
                }
            }
        }
        .environment(\.editMode, .constant(.active))
        .navigationTitle(title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("Cancel") { dismiss() }
            }
            ToolbarItem(placement: .confirmationAction) {
                Button("Done") {
                    arrangements.save(working, for: slug)
                    dismiss()
                }
                .fontWeight(.semibold)
            }
        }
        .sheet(isPresented: $showPalette) {
            NavigationStack {
                PaletteView { unit in working.append(ArrangedPrayer(unit)) }
            }
        }
        .task {
            // Seed from the saved arrangement, or from the printed office the
            // first time the reader opens the editor.
            guard !loaded else { return }
            loaded = true
            working = arrangements.arrangement(for: slug)
                ?? library.units(of: slug).map(ArrangedPrayer.init)
        }
    }

    @ViewBuilder
    private func row(_ prayer: ArrangedPrayer) -> some View {
        if let unit = library.unit(prayer) {
            VStack(alignment: .leading, spacing: 2) {
                Text(unit.title)
                    .font(Typeface.display(.body))
                if unit.pageSlug != slug, let from = library.page(unit.pageSlug)?.title {
                    Text(from)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.vertical, 2)
            // One element, not two: a prayer and the book it came from should
            // read as a single item to VoiceOver, and be a single drag target.
            .accessibilityElement(children: .combine)
            .accessibilityIdentifier("prayer.row")
        } else {
            // The content was regenerated and this heading is gone.
            Label("No longer in this edition", systemImage: "exclamationmark.triangle")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

/// The prayers available to add: all of A Little Prayer Book, grouped by the
/// section each comes from.
struct PaletteView: View {
    let onPick: (PrayerUnit) -> Void

    @EnvironmentObject private var library: Library
    @Environment(\.dismiss) private var dismiss
    @State private var search = ""

    private var groups: [(section: BookSection, units: [PrayerUnit])] {
        let all = library.palette()
        guard !search.isEmpty else { return all }
        return all.compactMap { group in
            let hits = group.units.filter {
                $0.title.localizedCaseInsensitiveContains(search)
            }
            return hits.isEmpty ? nil : (group.section, hits)
        }
    }

    var body: some View {
        List {
            ForEach(groups, id: \.section.id) { group in
                Section(group.section.title) {
                    ForEach(group.units) { unit in
                        Button {
                            onPick(unit)
                            dismiss()
                        } label: {
                            HStack {
                                Text(unit.title)
                                    .font(Typeface.display(.body))
                                    .foregroundStyle(.primary)
                                Spacer(minLength: 8)
                                Image(systemName: "plus")
                                    .font(.footnote.weight(.semibold))
                                    .foregroundStyle(Color.sanctuaryGold)
                            }
                        }
                    }
                }
            }
        }
        .searchable(text: $search, prompt: "Search prayers")
        .navigationTitle("Add a prayer")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("Cancel") { dismiss() }
            }
        }
    }
}
