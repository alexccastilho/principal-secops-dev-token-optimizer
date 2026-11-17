# Qt 6 — C++ and QML

Version policy: follow `versoes-e-fontes.md`. Use the newest Qt 6 LTS, or the LTS already installed on the project, and confirm the current LTS and its support dates at qt.io/blog before recommending one. Qt 5 no longer receives open source support. Read `gui-desktop.md` first for the rules that are not Qt-specific, and `gui-design.md` for the visual side.

Licensing: the open source build is LGPLv3 or GPLv3. Under LGPL you must let the user relink, which means dynamic linking. Under GPLv3, when your own application is GPLv3, you may link Qt statically and ship a single binary.

## Widgets or QML
* **Widgets** for data-dense desktop software: tables, trees, docking, menus, dialogs. Model and view is mature and carries millions of rows.
* **QML** for animated, custom-looking or touch-shaped interfaces. It starts slower, roughly 150 to 300 ms extra for the engine, and its `TableView` is less proven at scale.
* Mixing through `QQuickWidget` works and roughly doubles the build complexity. Start with one.
* Rule of thumb: if the centre of the app is a large list or table, Widgets. If it is a dashboard, a media surface or a kiosk, QML.

## Model and view, the part that decides performance
* Subclass `QAbstractItemModel`, or `QAbstractTableModel` for flat data, over the data you already hold. Never copy the data into the view.
* Implement `rowCount`, `columnCount`, `data` and `headerData`, plus `index` and `parent` for a tree, and `flags` for editing or dragging.
* `canFetchMore` and `fetchMore` for incremental loading, so opening a huge document paints immediately.
* `setUniformRowHeights(true)` on `QTreeView` when rows are the same height. It removes per-row measurement and is one of the largest single wins available.
* Custom appearance comes from `QStyledItemDelegate::paint`, not from `setIndexWidget`. A widget per row defeats the whole design.
* `QSortFilterProxyModel` is right for moderate data. It keeps a full index map, so past a few hundred thousand rows sort and filter inside the model instead.
* Wrap every structural change in `beginInsertRows` and `endInsertRows`, and the equivalents for removal and reset. Getting this wrong corrupts the view in ways that look random. Run `QAbstractItemModelTester` in debug builds; it catches the mistake at the source.
* Emit `dataChanged` over the narrowest range that changed, never over the whole model.
* **Sorting has two traps that both look like they work.** After reordering, `layoutChanged` alone leaves every persistent index pointing at the wrong row, which corrupts the selection and any open editor: call `persistentIndexList`, remap, and `changePersistentIndex` between the two signals, or use `beginResetModel` when losing the selection is acceptable. And the comparator handed to `std::sort` must be a strict weak ordering: inverting with `return ascending ? less : !less` claims `a < b` and `b < a` for equal elements, which is undefined behaviour and does crash on real data. Swap the operands instead.
* Sort an index permutation rather than the data, so row-to-record mapping stays stable and nothing above the model is invalidated.

## Threads
* Every `QObject` has thread affinity. A widget is only ever touched from the GUI thread.
* **A `QThread` object itself lives in the thread that created it, not in the thread it starts.** So `QMetaObject::invokeMethod(&myThread, ...)` and a slot connected on the `QThread` subclass both run on the GUI thread, and the work you meant to move never moved. Move a separate worker `QObject` with `moveToThread`, and connect to that object.
* For ongoing work, a worker `QObject` moved with `moveToThread`. For a one-shot job, `QtConcurrent::run` with a `QFutureWatcher` to get the result back on the GUI thread.
* Cross-thread communication is queued signals, which are safe by construction. Custom argument types need `qRegisterMetaType`.
* `QThread::sleep` in the GUI thread and `QApplication::processEvents` are both symptoms of work that belongs on a thread.

## Drag and drop
* Receiving: `setAcceptDrops(true)`, then override `dragEnterEvent` to accept only the MIME types you handle, and `dropEvent` to act. File paths arrive through `QMimeData::urls()`.
* Sending: build a `QDrag` with a `QMimeData`. A receiving application expects real files, which means `text/uri-list` populated with paths that exist by the time it reads them.
* Delayed extraction, so you do not write gigabytes before knowing where the drop lands: subclass `QMimeData` and override `retrieveData`, which Qt calls when the target actually requests a format. On Windows, register the file-contents formats through Qt's Windows MIME converter class so Explorer can pull the bytes on demand.
* **Do not extract inside `startDrag` before calling `exec`.** That runs on the GUI thread while the system drag is starting, so the whole desktop's drag feedback freezes for as long as the extraction takes, and the user sees a hang at the exact moment they expect responsiveness. Use the delayed transfer above, or extract on a worker while showing progress.
* A temporary directory created per drag has to be deleted. Keeping every one alive for the lifetime of the process, which is the easy way to make the paths stay valid, fills the disk over a session.
* `QDrag::exec` runs a nested event loop and blocks. Do no heavy work inside it and no heavy work in `retrieveData` on the GUI thread.

## Appearance
* Qt Style Sheets for theming. Scope the selectors to the classes you mean; a stylesheet applied to everything is slow and breaks native behaviour.
* Follow the system light or dark setting through `QGuiApplication::styleHints()->colorScheme()`, and connect to its change signal so the app switches without a restart.
* HiDPI scaling is automatic in Qt 6. Ship SVG icons, and on Linux respect the icon theme through `QIcon::fromTheme` with a bundled fallback.
* Take the UI font from `QFontDatabase::systemFont(QFontDatabase::GeneralFont)` rather than naming a family.
* Size from `QFontMetrics` and layout spacing, not hardcoded pixels, or the interface breaks at 150% scale.

## Security
* Qt carries a large parsing surface: image formats, SVG, network, and every plugin present at run time. In a static or trimmed build, include only the plugins you use.
* `QProcess` with `setProgram` and `setArguments`. Never the single-string overload, which goes through a shell on some platforms.
* `QSqlQuery` with `prepare` and `bindValue`. String-built SQL is injection in Qt exactly as anywhere else.
* `QNetworkAccessManager` verifies TLS by default. Never call `ignoreSslErrors`.
* `QSettings` is configuration, not a secret store. It is plain text or the registry.
* `QTemporaryFile` and `QTemporaryDir` create with safe permissions and clean up; hand-built temp paths in `/tmp` usually do neither.
* QML: never load QML or JavaScript from the network. It is code execution, and there is no sandbox around it.

## Build and deployment
* CMake with `qt_standard_project_setup`, `qt_add_executable` and `qt_add_qml_module`. `qmake` is legacy for new work.
* `windeployqt` on Windows and `linuxdeployqt` or CQtDeployer on Linux gather the runtime. Flatpak and AppImage are the friendlier Linux paths.
* Set `QT_DISABLE_DEPRECATED_UP_TO` so deprecated API fails the build rather than rotting quietly.
* A static Qt under GPLv3 gives one file and the fastest cold start, at the cost of building Qt from source once.

## Testing
* Qt Test for unit tests, `QSignalSpy` to assert on signals, `QAbstractItemModelTester` on every model.
* In CI run headless with `QT_QPA_PLATFORM=offscreen`, so a GUI smoke test needs no display server.
