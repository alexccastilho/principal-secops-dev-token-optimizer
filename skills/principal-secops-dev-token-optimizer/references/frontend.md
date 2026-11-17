# HTML5 and CSS — W3C / WHATWG standards

## HTML
* Semantic structure: `<header> <nav> <main> <section> <article> <footer>`. One `<h1>` per page, heading levels in order, no skipping.
* Accessibility, WCAG 2.2 AA baseline: `alt` on every image (`alt=""` when decorative), `<label for>` tied to every input, `aria-label` only where no visible label exists, visible focus indicator, contrast at least 4.5:1, targets at least 24x24 CSS pixels, no keyboard trap.
* Forms: correct `type` (`email`, `tel`, `number`, `date`), `required` / `min` / `max` / `pattern` for native validation, `autocomplete` attributes. Client validation is convenience; server validation is the real one and is never optional.
* `<meta charset="utf-8">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `lang="pt-BR"` on `<html>` for Brazilian content.
* No inline JS (`onclick=""`), no inline CSS (`style=""`). Scripts with `defer`. This is also what makes a strict CSP possible.
* Third-party embeds in an `<iframe>` with `sandbox` and only the permissions they need.

## CSS
* Custom properties for palette and spacing (`:root { --primary: ... }`). Mobile-first media queries.
* Layout: Grid for two dimensions, Flexbox for one. No floats for layout, no fixed pixel heights on text containers.
* `rem` for typography and spacing, `%` or `fr` for layout, `clamp()` for fluid type where it helps.
* Class naming consistent, kebab-case or BEM, following whatever the project already uses.
* No `!important` except to override a third-party library. No selector chains deeper than three levels.
* `prefers-reduced-motion` respected. Transitions on `transform` and `opacity` only, since those are GPU-friendly.
* Modern selectors when supported: `:has()`, `:is()`, container queries, `light-dark()`. Check support before relying on one for layout.

## Security in the browser
* Anything in front-end code is public: no keys, no tokens, no business rules that matter.
* Never `innerHTML` with data that came from a user or an API. Use `textContent`, or sanitize before inserting.
* Never build a URL for `location`, `fetch` or an `<a href>` from unvalidated input. `javascript:` in an href is XSS.
* External scripts from a CDN carry `integrity` (SRI) and `crossorigin`. A compromised CDN script owns the page.
* `target="_blank"` gets `rel="noopener noreferrer"`.
* Data in `localStorage` is readable by any script on the page, so no session tokens there.

## Performance
* Images: modern format (WebP or AVIF), `loading="lazy"` below the fold, explicit `width` and `height` to avoid layout shift, `srcset` for responsive sizes.
* Minimize render-blocking: critical CSS inline only when measured, fonts with `font-display: swap`, self-hosted fonts when possible.
* One CSS file and one JS file per page unless a bundler already exists. Follow the project's pipeline, do not introduce one.
* Measure with Lighthouse before and after. Report the number, not an adjective.
* Core Web Vitals are the targets: Largest Contentful Paint (LCP) under 2.5 s, Interaction to Next Paint (INP) under 200 ms, Cumulative Layout Shift (CLS) under 0.1, measured at the 75th percentile (web.dev/vitals).
* Serve text assets compressed (gzip or Brotli), static files with long `Cache-Control` only when the file name changes with the content, and HTML with a short or no-store policy. Minify CSS and JS in production; a CDN for static files when the audience is spread out.
