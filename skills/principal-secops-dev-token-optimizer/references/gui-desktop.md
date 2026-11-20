# Desktop GUI: choosing a toolkit, and the rules that outlive the choice

Version policy: follow `versoes-e-fontes.md`. Toolkit versions, licences and start-up figures named here are examples (the comparison table was not re-checked in 2.2.0); read the version the project pins before using a feature gated "(X.Y+)".

Toolkit specifics live in `qt.md` and `gui-outros.md`. Visual decisions live in `gui-design.md`. This file is what applies whatever you pick.

## Choosing a toolkit

| Toolkit | Language | Cold start | Huge lists | Native feel Win + Linux | Licence |
|---|---|---|---|---|---|
| Qt 6 | C++, QML optional | ~40 ms | Model/view, proven at millions of rows | Both | LGPLv3 / GPLv3 |
| Slint | Rust, C++ | ~20 ms | Good, fewer ready-made primitives | Both, own look | GPLv3, royalty-free (not embedded) or commercial |
| Avalonia | C# | ~300 ms | Good | Both, own look | MIT |
| GTK4 + libadwaita | C, Rust, Python | ~80 ms | GtkColumnView is strong | Excellent Linux, alien on Windows | LGPL |
| Flutter | Dart | ~200 ms | Good | Neither, its own look everywhere | BSD |
| Tauri | Rust + web UI | ~150 ms | Needs a windowing library | Webview differs per OS | MIT |
| Electron | JS + web UI | ~600 ms | Needs a windowing library | Consistent, not native | MIT |
| wxWidgets | C++ | ~40 ms | Adequate | Truly native, dated defaults | wxWindows, LGPL-like |

Decision rules that hold more often than not:

* **Match the language the core is already in.** A toolkit in a second language buys an FFI boundary on the hottest path plus a second toolchain. That cost usually outweighs any framework advantage.
* **Anything launched from a context menu or a hotkey lives or dies on cold start.** That rules out a runtime which has to warm up, whatever its other merits.
* **A webview is the wrong shape for a data-dense desktop tool.** WebView2 and WebKitGTK behave differently, and a large table in the DOM needs work to reach what a native model/view gives for free. It fits well when the UI is content-shaped and the team is a web team.
* GTK on Windows and Qt inside GNOME both work, but neither looks like it belongs. Weigh where the users actually are.
* A GPL project can link Qt statically under GPLv3, which LGPL would not allow. One binary, faster start, no DLL search order to worry about.

## Performance budgets
Numbers, not adjectives. Measure against these and report the measurement.

* **Cold start to first paint:** under 300 ms for a normal app, under 100 ms for anything invoked from a context menu or a hotkey.
* **Frame budget:** 16.7 ms at 60 Hz, 6.9 ms at 144 Hz. Any single piece of work on the UI thread longer than that drops a frame, and dropped frames are what the user calls travando.
* **Input acknowledgement:** 100 ms. Past that the action stops feeling direct.
* **Lists:** anything that can exceed roughly 1000 rows must be virtualised. There is no optimise-it-later here, because it decides the architecture.
* **Idle memory:** set a target and watch it. A file tool sitting at 400 MB idle is a defect even when nothing feels slow.

## Virtualisation
The most common desktop performance failure is one widget per data item. It works in a demo with 50 rows and dies at 50 000. The distinction to get right in every toolkit is item widgets versus model and view.

* **Qt:** `QAbstractItemModel` with `QTreeView` or `QTableView`. Not `QTableWidget`, `QListWidget` or `QTreeWidget`, which allocate an object per cell.
* **Avalonia and WPF:** `ItemsControl` over a `VirtualizingStackPanel`. Check that a wrapping `ScrollViewer` or `WrapPanel` has not silently disabled virtualisation.
* **GTK4:** `GtkColumnView` or `GtkListView` over a `GListModel`. Not `GtkListBox`, and not a `GtkTreeView` preloaded into a `GtkListStore` (both deprecated since GTK 4.10).
* **Slint:** `ListView` bound to a `Model`, never a loop over a materialised array.
* **Web, Electron, Tauri:** a windowing library such as TanStack Virtual. DOM nodes proportional to the viewport, never to the data.

Then, in any toolkit:

* Sort and filter the model. Never rebuild the view to reorder it.
* Fetch metadata lazily, for visible rows only. Reading 300 000 file dates up front is the same mistake wearing different clothes.
* Keep row height fixed where you can. Variable heights force measuring everything.

## Threading
* **The UI thread paints.** It does no I/O, no decompression, no hashing, no network call, no directory walk.
* Every operation that can pass one second is cancellable and reports progress.
* Touch UI objects only from the UI thread, through the toolkit mechanism for it: queued signals in Qt, `Dispatcher` in Avalonia, `g_idle_add` in GTK, `invoke_from_event_loop` in Slint.
* **Never pump the event loop to keep the UI alive during blocking work.** `QApplication::processEvents`, `DoEvents` and hand-written loops over the event queue all reenter your own handlers, and produce bugs that reproduce once a week and never in a debugger. Move the work to a thread instead.
* Batch UI updates. One signal per file across 300 000 files costs more than the work itself. Coalesce into a single update every 60 to 100 ms.

## Drag and drop
Both directions are required for a file tool, and they are not symmetric.

**Dropping into the app**

* Accept only the formats you handle, and say so on drag-enter with visible feedback. Silence reads as broken.
* A drop payload is untrusted input, exactly like a command-line argument. Paths may not exist, may sit on a network share that blocks for 30 seconds, may be symlinks, may be a directory holding a million children.
* Resolve and validate on a worker thread, not inside the drop handler.

**Dragging out of the app**

This is the half that gets skipped, and it is the harder one, because the receiving application expects a real file on disk.

* Two strategies. Extract to a temporary directory and hand over the paths: simple, but it spends disk and time before the user knows where the drop lands. Or use a delayed transfer, so extraction happens only when the target actually asks for the bytes.
* Delayed transfer on Windows: `CFSTR_FILEDESCRIPTOR` plus `CFSTR_FILECONTENTS` on the data object. On Linux and XDG desktops: the XdndDirectSave protocol, with `text/uri-list` as the fallback.
* Never block the UI thread producing drag data. The system drag loop is already running on it, so blocking freezes drag feedback across the whole desktop.
* Clean up temporary files from a drag that was cancelled, or dropped somewhere that never read them.

## Platform integration
* **HiDPI:** per-monitor scaling, including fractional scales such as 125% and 150% on Windows and Wayland. Test at 200%. Ship vector icons, or bitmaps at 1x, 2x and 3x.
* **System theme:** follow the OS light or dark setting, and follow a change at run time without a restart. Honour the accent colour and the reduced-motion setting where the platform exposes them.
* **Native dialogs** for open, save and print. A hand-rolled file picker never matches the shell for places, search and permissions.
* **Keyboard:** every action reachable without a mouse, a visible focus ring, a sane tab order, and the platform conventions (F2 to rename and Delete to remove on Windows, the desktop convention on Linux).
* **Accessibility:** the toolkit must expose an accessibility tree, UI Automation on Windows and AT-SPI on Linux. A custom-drawn control exposes nothing until you implement it, which is a real and often forgotten cost of drawing your own widgets.
* **Internationalisation:** externalise every string, allow 30% growth for Portuguese and German, format dates and numbers by locale instead of by hand, and verify right-to-left before promising it.
* **Shell integration:** file associations, context-menu entries, recent files, single-instance behaviour and jump lists belong to the installer and the platform, not to the main window.

## Security specific to desktop apps
The web rules do not transfer. These are the ones that apply.

* Command-line arguments and file paths handed to the app are attacker-controlled once the app is registered for a file type. Anyone can craft a document and mail it.
* **Single-instance IPC:** a named pipe or Unix socket that any local process can reach is an attack surface. Authenticate the peer, accept a narrow set of messages, never expose a general command channel.
* **Custom URL schemes** are registered system wide, so any web page can invoke them. Treat every parameter as hostile, and never let one choose a file to execute.
* Clipboard content is readable by every process on the machine. Keep secrets out of it, and clear it after use where the platform allows.
* Never build a shell command from a filename. Use the process API with separate arguments.
* Verify a signature before applying an update, without exception.
* **Embedded webview:** context isolation on, node integration off, sandbox on, navigation restricted to an allowlist, web security never disabled, and no user content rendered through `innerHTML`.

## Packaging
* Windows: MSI, Inno Setup or NSIS, code signed. Prefer a per-user install so it does not demand administrator rights.
* Linux: deb and rpm, plus Flatpak or AppImage for reach. Under Flatpak the sandbox routes filesystem access through portals, which changes how file dialogs behave, so test inside the sandbox and not only outside it.
* Ship what you link. Static linking, where the licence allows it, gives one file and the fastest start.

## Testing a GUI
* Keep logic out of the view. A model you can test without opening a window is most of the testability you will get.
* One automated smoke test per OS in CI: launch, open a document, close. It catches missing libraries and packaging faults that no unit test sees.
* Test with the pathological dataset, not the demo one. The 300 000-row case is the requirement, not an edge case.
* Test at 200% scale, in dark mode, and with the longest locale.

## Pre-delivery checklist (graphical interface)
Run this on top of the gate in `SKILL.md`.

```
- [ ] Any list that can pass 1000 rows uses a virtualised model, not one widget per item
- [ ] No I/O, decompression or hashing on the UI thread; long work cancellable with progress
- [ ] Drag and drop works in both directions, and produces no work on the UI thread
- [ ] Follows the system light or dark setting, and changes without a restart
- [ ] Readable at 200% scale and with the longest string in the target language
- [ ] Empty, loading and error states designed, not only the full one
- [ ] Keyboard reaches every action, focus is visible
- [ ] Spacing and type come from the scale, no arbitrary values
```
