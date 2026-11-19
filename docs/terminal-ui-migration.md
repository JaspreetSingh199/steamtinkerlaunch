# STL-Steam terminal UI migration

## Decision

Replace YAD/GTK UI dependencies with `dialog` (ncurses), using a small internal wrapper layer to keep UI behavior centralized. The migration is intentionally incremental; do not globally replace YAD strings with dialog commands because the option semantics, output format, cancellation codes, and widget types differ.

## Inventory (source audit)

The main Bash executable contains roughly 82 YAD command invocations. UI patterns include:

- Form dialogs (single/multiple fields, numeric fields, editable values)
- Checklist and multi-column list dialogs
- File/directory pickers
- Question/info/error messages
- Progress/status windows fed by subprocess output
- Notifications
- Icon directory browsers
- HTML/wiki views
- Custom buttons and window geometry flags
- First-field actions and callback behavior

Several of these have no direct one-to-one dialog equivalent (HTML/wiki, notification, image display, icon browser, custom callback actions). These need redesigned terminal flows rather than mechanical translations.

## Wrapper design

Create a single `stl-ui` Bash helper (or sourced module) that exposes stable operations:

- `ui_msg` / `ui_error` / `ui_question`
- `ui_menu`
- `ui_checklist`
- `ui_input` / `ui_form`
- `ui_file` / `ui_directory`
- `ui_progress` / `ui_log`

The wrapper should use `dialog` when available, with a clear error and actionable dependency message if unavailable. It should preserve return-code semantics for OK, Cancel, ESC, and failure. It should keep stdout reserved for selected values and stderr for UI rendering/logging where practical.

## Migration stages

1. **Audit:** categorize each YAD call site and identify output parsing/callback assumptions.
2. **Foundation:** implement wrapper and unit tests using fake dialog commands; no production call sites migrated yet.
3. **Simple dialogs:** migrate message/question/menu and progress/status dialogs.
4. **Lists/forms:** migrate checklist, multi-column lists, form inputs, file/directory selection.
5. **Special UI:** replace wiki/html, image/icon browsing, notification and callback behavior with terminal-friendly alternatives or remove them where nonessential.
6. **Remove YAD:** delete YAD download/config/dependency code, CLI `yad` command, YAD AppImage references, and YAD-specific docs only after no call sites remain.
7. **CI:** add ShellCheck and tests for the wrapper, and grep-based guard that production code contains no YAD runtime invocation or dependency (allow historical docs if explicitly marked).

## Constraints

- Keep the migration functional, not just syntactic.
- Preserve keyboard navigation and accessibility for terminal users.
- Do not silently discard menu actions or fields.
- Cancellation must not be treated as an empty successful selection.
- Do not change unrelated game, Proton, Vortex, MO2, or prefix logic during UI migration.
- Test each migrated dialog category before moving on.
- GTK/YAD removal should be complete only when dependency installation, binary downloads, config, checks, runtime calls, and help text have all been audited.

## Initial scope

The first user-facing target is the Skyrim-focused STL-Steam branch, but the UI foundation should remain reusable across STL rather than hardcoding Skyrim-specific dialog behavior.
