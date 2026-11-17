# Visual design — making an interface look deliberate

Applies to desktop and web. This is what separates an interface that looks designed from one that looks assembled. Almost none of it requires talent; all of it requires consistency.

## The rule that does most of the work
Pick a scale and never leave it. Arbitrary values are what read as amateur: 13px here, 15px there, 7px of padding. Define the scale once and use only its steps.

* **Spacing:** one base unit, 4 px or 8 px. Every margin, padding and gap is a multiple: 4, 8, 12, 16, 24, 32, 48, 64. Nothing else.
* **Type:** five to seven sizes, not fifteen. A working ramp: 12, 14, 16, 20, 24, 32. Body is 14 px on desktop, 16 px on web.
* **Weight:** two or three. 400 for body, 500 or 600 for emphasis, 700 rarely. Never synthesise bold.
* **Radius:** two values, one for controls and one for containers. Consistency matters more than the number.

## Typography
* One UI typeface plus one monospace for code and for numbers that must align. Two families is a design; four is a ransom note.
* Default to the platform UI font: Segoe UI Variable on Windows, the system stack on Linux (Cantarell, Inter, Noto Sans), SF on macOS. It is instantly familiar and costs no download. Ship a font only when the brand genuinely needs it, and check its licence.
* Line height 1.4 to 1.6 for body, 1.1 to 1.25 for headings. Tight headings, loose paragraphs.
* Line length 45 to 75 characters for anything meant to be read. Wider and the eye loses its place returning to the next line.
* Tabular figures (`font-variant-numeric: tabular-nums`, or the font's tnum feature) for every column of numbers. One line of CSS, and the table stops looking homemade.
* Never centre long text. Never justify in a UI: the whitespace rivers look worse than a ragged edge.

## Colour
* Work in tokens, never literal values inside components: `surface`, `surface-raised`, `border`, `text-primary`, `text-secondary`, `accent`, `danger`, `warning`, `success`.
* One accent colour. A second is a decision that needs justifying. Semantic colours are not accents.
* Contrast: at least 4.5:1 for body text, 3:1 for large text and for the visible boundary of any interactive control. Measure it, do not judge it by eye.
* Grey is not one colour. Tint the greys slightly toward the accent hue so they read as chosen rather than muddy.
* **Dark mode is not inverted light mode.** Drop saturation, avoid pure black for surfaces (use the #16181C to #1E2126 range), avoid pure white for text (around #E6E8EA). Maximum contrast at both ends causes halation and eye strain.
* Never carry meaning in colour alone. Pair it with an icon, a label or a shape.

## Density and layout
* Choose density on purpose. A data tool wants compact rows, 24 to 28 px. A consumer app wants comfortable ones, 36 to 44 px. Offer a toggle when the audience is both.
* Align to a grid. The left edges of labels, inputs and icons either line up or the eye notices without knowing why.
* Group by proximity before reaching for a border. A box drawn around everything is what makes an interface look like 2005.
* Cramped is the common failure, not sparse. Whitespace is a feature.
* Give every screen one primary action. A toolbar with thirty equal buttons has no hierarchy; three primary actions plus an overflow menu does.

## Icons
* One icon set, one style, one stroke weight, one grid size. Mixing filled and outlined from two libraries is visible immediately.
* Label icons unless the symbol is genuinely universal (close, play, search). An icon-only toolbar is a memory test.
* Match optical weight to the text beside it, not geometric size.

## Motion
* Motion exists to show causality: where a thing came from and where it went. Decorative motion is noise.
* 120 to 200 ms for a small state change, 200 to 300 ms for a panel or dialog. Past 400 ms it feels slow however pretty it is.
* Ease-out entering, ease-in leaving. Linear only for continuous progress.
* Animate transform and opacity. Animating layout properties forces reflow and causes jank.
* Honour the system reduced-motion setting. It is an accessibility requirement, not a preference.

## The states everyone forgets
Every view needs four designs. Shipping only the last is what makes software feel unfinished.

* **Empty:** what to do first, and a control that does it. Never a blank panel.
* **Loading:** a skeleton where the content will land, not a spinner in the void. Under 200 ms show nothing at all, because a flash reads worse than a wait.
* **Error:** what happened in plain language plus the one action that fixes it. Never a bare code.
* **Full:** the one everyone remembers to design.

Then focus, hover, active, disabled and selected for every interactive element. Focus especially: it is invisible to a mouse user and the entire interface to a keyboard user.

## Perceived speed
Perceived speed is a design property at least as much as an engineering one.

* Acknowledge input within 100 ms, even if only by showing the control depressed. That is the threshold where an action feels direct rather than reported.
* Show honest progress once work passes 1 second. A bar that parks at 90% destroys trust permanently.
* Render what you already have while the rest loads. A list filling in row by row feels faster than one that appears complete a second later.
* Keep layout stable. Content that jumps while loading reads as slower than content that appears in place.

## Checking the result
* View it at 200% zoom and on a 1366x768 screen. Most designs break on one of the two.
* View it in dark mode after designing in light, and the reverse.
* View it with the longest realistic string, not "Nome". Portuguese and German run roughly 30% longer than English.
* Screenshot it, halve the size, squint. The hierarchy should survive. If everything reads at the same weight, nothing is emphasised.
