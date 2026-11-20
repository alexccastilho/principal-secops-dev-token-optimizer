# GUI toolkits other than Qt

Version policy: follow `versoes-e-fontes.md`. Each toolkit section names its release page; read the version the project pins before using a feature gated "(X.Y+)".

Rule for any toolkit here: apply `gui-desktop.md` for the cross-cutting rules and `gui-design.md` for the visual ones, then the toolkit notes below. Qt has its own reference in `qt.md`.

## Slint (Rust, C++)
* Declarative `.slint` markup compiled ahead of time, so start-up is very fast and the binary is small. Good fit when the core is already Rust.
* Lists: `ListView` bound to a `Model` (`VecModel`, or your own `Model` implementation for lazy data). A `for` over a plain array materialises everything, which is the mistake to avoid.
* Threads: the UI runs on one thread. Come back with `invoke_from_event_loop`, or a `Weak` handle plus `upgrade_in_event_loop`.
* Drag and drop within the application arrived in 1.17 (`DragArea`, `DropArea`). Dragging to and from other applications was not supported in that release and later release notes do not announce it; check the current release notes and test on each target OS before promising it, which is the main reason to think twice for a file manager.
* Licence: GPLv3, a Royalty-Free licence (excludes embedded systems), or commercial tiers. Fine for a GPL project, needs checking for anything else.

## Avalonia (C# / .NET)
* XAML close to WPF, genuinely cross platform, MIT licensed. The best of the managed options for desktop.
* Lists: `ItemsControl` with `VirtualizingStackPanel`. Wrapping the control in a `ScrollViewer` or swapping in a `WrapPanel` silently turns virtualisation off, which is the classic Avalonia and WPF performance bug.
* Threads: never touch UI off the dispatcher. `Dispatcher.UIThread.Post` or `InvokeAsync`. `async`/`await` keeps the context for you when you do not call `.Result` or `.Wait()`, which deadlock.
* Drag and drop: `DragDrop.DoDragDropAsync` with a `DataTransfer`, files through `DataFormat.File` and `TryGetFiles()` (12+). Avalonia 11 code uses `DragDrop.DoDragDrop` with a `DataObject` and `DataFormats.Files`; that API is removed in 12, so migrate it when upgrading.
* Theming: Fluent theme, plus resource dictionaries for tokens. Follows the OS dark setting through `ActualThemeVariant`.
* Start-up: use NativeAOT or ReadyToRun publishing, or first paint lands near half a second. Self-contained publishing removes the runtime dependency at the cost of binary size.
* Security: `dotnet list package --vulnerable` in the build, never `BinaryFormatter` (Avalonia 12 no longer uses it for the clipboard; serialize custom clipboard objects yourself, JSON for example), and no secrets in `appsettings.json` inside the repo.

## GTK4 and libadwaita (C, Rust via gtk-rs, Python)
* The right choice for something meant to feel native inside GNOME, and it looks foreign on Windows. Building for Windows is possible through MSYS2 and is real work.
* Lists: `GtkColumnView` or `GtkListView` over a `GListModel`, with a factory that recycles rows. `GtkTreeView` with `GtkListStore` is the legacy path, loads everything, and is deprecated since GTK 4.10.
* Threads: GTK is single threaded. Return to the main loop with `g_idle_add` or `glib::MainContext::spawn_local`.
* Drag and drop: `GtkDragSource` and `GtkDropTarget` in GTK4, with `GdkContentProvider`. The GTK3 API is entirely different, so check which version a snippet targets.
* Theming: libadwaita follows the GNOME palette and the system dark preference. Heavily restyling libadwaita fights the platform; if you want a custom look, GTK is the wrong pick.
* Packaging: Flatpak is the natural target. Inside the sandbox, file access goes through portals, so file dialogs behave differently than in a plain build.

## Flutter (Dart)
* Draws every pixel itself, so it looks identical everywhere and native nowhere. Excellent for a branded look, poor for something that should feel like a system tool.
* Lists: `ListView.builder` and `ListView.separated` build lazily. A `ListView(children: [...])` with a built list does not.
* Threads: `Isolate` for CPU work, since the UI isolate blocking is what drops frames. `compute()` for the simple case.
* Desktop integration (context menus, shell entries, drag out to the file manager) leans on third-party plugins of uneven quality. Check maintenance before depending on one.
* Binary size is large and start-up is middling. Both are acceptable for an application, not for a tool launched constantly.

## Tauri (Rust core, web UI)
* Small binary because it uses the platform webview, which is also the catch: WebView2 on Windows and WebKitGTK on Linux differ in CSS support, performance and bugs. Test on both from day one, not at the end.
* Lists: the DOM is not virtualised for you. Use a windowing library so node count follows the viewport, never the data.
* Security is the main thing to get right, because the boundary is real: expose the narrowest possible set of commands, grant each window only the permissions it needs through capabilities (Tauri 2; Tauri 1 used an `allowlist`), never list remote URLs in a capability's `remote` field unless unavoidable, and validate every argument in Rust as untrusted. The frontend is not a trusted caller.
* Never load remote content into the main window. If you must render remote HTML, use a separate window with no command access.
* Content Security Policy applies exactly as on the web, and it is worth setting strictly.

## Electron (JavaScript, Chromium)
* Heaviest start-up and memory of the options here, and the most mature ecosystem. It earns its place when the team is a web team and the UI is content-shaped.
* Security is not optional. Keep the defaults: `nodeIntegration: false` (5+), `contextIsolation: true` (12+), `sandbox: true` (20+), and a `preload` script exposing a narrow API through `contextBridge`. Never `webSecurity: false`. Load the app through a custom protocol rather than `file://`, and turn off unneeded fuses.
* Validate every IPC message and its sender in the main process. A renderer is the untrusted side, and any remote content it loads is running in it.
* Restrict navigation and window creation with `will-navigate` and `setWindowOpenHandler`. Open external links in the system browser.
* Lists: same as Tauri, virtualise in the DOM.
* Keep Electron current. Its release cadence follows Chromium, so an old Electron is an old browser with known holes.

## wxWidgets (C++)
* Wraps real native controls, so it looks genuinely native on each platform, including the parts that feel dated on Windows.
* Lists: `wxDataViewCtrl` with a `wxDataViewVirtualListModel`, or `wxListCtrl` in `wxLC_VIRTUAL` mode. The non-virtual modes hold every item.
* Threads: only the main thread touches UI. Use `wxQueueEvent` or `CallAfter`.
* A reasonable choice when native appearance matters more than visual control, and when the project is already C++ but does not want Qt's size.

## Windows-only and macOS-only
* **WinUI 3 / WPF:** for Windows-only tools. WPF is mature and still fine; WinUI 3 is current but its deployment story is more involved. Both virtualise through `VirtualizingStackPanel` with the same disabling traps as Avalonia.
* **SwiftUI / AppKit:** for macOS-only. SwiftUI `List` and `LazyVStack` are lazy; a plain `VStack` is not.
* Choosing one of these means writing the UI again for the other platform. That is sometimes the right call, and it should be a decision rather than an accident.

## Immediate-mode (Dear ImGui, egui)
* The whole UI is rebuilt every frame, which makes them excellent for tools, debug overlays and editors, and wrong for a consumer application.
* They redraw continuously by default, which keeps a GPU busy and drains a laptop battery. Configure them to redraw on demand for anything that stays open.
* Accessibility differs: egui exposes a tree through AccessKit (on by default in `eframe` on native platforms; plain egui integrations call `Context::enable_accesskit()`), while Dear ImGui exposes no platform accessibility tree, so a screen reader sees nothing. Test with a real screen reader where accessibility is required.
* No native menus, no native dialogs, no real drag and drop with the OS.

## Python desktop (PySide6, Tkinter)
* **PySide6** is Qt with official Python bindings under LGPL, so `qt.md` applies almost unchanged. Good for internal tools; packaging with PyInstaller produces a large, slow-starting binary.
* **Tkinter** ships with Python and looks it. Acceptable for a script with a dialog, not for a product.
* On the default build, the GIL means CPU work must go to `multiprocessing` or a native extension, not to threads, or the interface stops repainting. The free-threaded build is officially supported but optional (3.14+), and only helps when every dependency supports it.
