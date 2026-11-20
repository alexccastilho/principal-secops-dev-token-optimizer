# Frontend: HTML, CSS and browser JavaScript (WHATWG, W3C, WCAG)

Version policy: follow `versoes-e-fontes.md`. Browsers are evergreen, so the question is support, not version: check the feature's Baseline status on MDN (or caniuse.com) against the audience the project declares (`browserslist` in `package.json`, analytics, or the user's answer). "Baseline widely available" is safe without fallback; "newly available" needs a fallback for older devices; "limited availability" is progressive enhancement only. Standards editions: WCAG at w3.org/WAI/standards-guidelines/wcag, WebAssembly at webassembly.org/specs. Server-side framework rules live in the language files; this file is what runs in the browser.

## Contents
- Standards and style
- Accessibility
- Security in the browser
- Content Security Policy
- WebAssembly security notes
- Exceptional conditions
- Supply chain
- Tuning
- Traps and fixes
- Legacy front ends: safe maintenance

## Standards and style
* Semantic structure: `<header> <nav> <main> <section> <article> <footer>`. One `<h1>`, heading levels in order. `<button>` for actions, `<a href>` for navigation.
* `<meta charset="utf-8">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `lang="pt-BR"` on `<html>` for Brazilian content.
* Forms: correct `type`, `required`/`min`/`max`/`pattern`, `autocomplete`. Client validation is convenience; the server validates for real.
* No inline JS (`onclick=""`) and no inline `style=""`: required for a strict CSP. Scripts with `defer` or `type="module"`.
* CSS: custom properties for palette and spacing, mobile-first, Grid for two dimensions and Flexbox for one, `rem` for type, `clamp()` for fluid sizes. Follow the project's naming (BEM or kebab-case). No `!important` except over third-party CSS.
* Modern features (`:has()`, container queries, `light-dark()`, `<dialog>`, popover) only after checking Baseline; layout must not depend on a limited-availability feature.
* Lint: the project's ESLint and Stylelint config; HTML validated with the W3C validator when there is no framework.

## Accessibility
* Baseline target WCAG 2.2 level AA (the current Recommendation, also ISO/IEC 40500:2025). WCAG 3.0 is a draft: do not cite it as a requirement.
* `alt` on every image (`alt=""` when decorative); a visible `<label for>` on every input; `aria-*` only when no native element does the job.
* Keyboard: every action reachable with Tab and Enter/Space, visible focus indicator, no keyboard trap, focus not hidden under sticky headers.
* Contrast at least 4.5:1 for text (3:1 for large text and UI parts); targets at least 24x24 CSS pixels; `prefers-reduced-motion` respected.
* Errors announced in text next to the field, not by colour alone. Do not ask the user to retype information already given in the same flow.
* Legal context: Brazil's Lei Brasileira de Inclusão (Lei 13.146/2015) covers sites of companies and public bodies; selling to EU consumers brings the European Accessibility Act (applies since 28 June 2025). Say "consulte um advogado" for the legal reading, but build to WCAG 2.2 AA.
* Check with axe DevTools or Lighthouse accessibility audit, then a manual keyboard pass. An automated score is not compliance.

## Security in the browser
* Everything shipped to the browser is public: no API keys with write power, no secrets, no business rules that matter. Bundler env prefixes (`VITE_`, `NEXT_PUBLIC_`) publish the value.
* DOM XSS: never `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` with data from a user, URL or API. Use `textContent` or build nodes. When HTML must be rendered, sanitize with DOMPurify, or `element.setHTML()` where supported (limited availability, so keep a fallback).
* Trusted Types (Baseline newly available in 2026): with the CSP `require-trusted-types-for 'script'`, a raw string assigned to `innerHTML` throws, which finds every sink. Start in report-only mode.
* URLs: never put unvalidated input in `location`, `href`, `src` or `fetch`. Allow only `https:` (and `mailto:` where needed); `javascript:` in an href is XSS. Parse with `new URL()` and check `protocol` and `host`.
* `postMessage`: always pass an explicit target origin; on receive, check `event.origin` against an allowlist before using `event.data`.
* Storage: `localStorage`/`sessionStorage` are readable by any script on the page, so no session tokens there; prefer `HttpOnly` cookies set by the server.
* Links: `target="_blank"` already implies `noopener` in modern browsers; add `rel="noopener noreferrer"` when old browsers matter or the Referer must not leak.
* Third-party embeds in `<iframe sandbox>` with only the permissions they need; `allow` lists only the features used.
* Clickjacking: CSP `frame-ancestors 'none'` (or `'self'`) from the server; `X-Frame-Options` for old browsers.

## Content Security Policy
* Strict CSP, sent as an HTTP header by the server: `script-src 'nonce-{RANDOM}' 'strict-dynamic'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'`. The nonce is new and unpredictable on every response; static sites use `'sha256-...'` hashes instead.
* Never `'unsafe-inline'` or `'unsafe-eval'` in `script-src`. When a nonce or hash is present, browsers ignore `'unsafe-inline'` anyway.
* Roll out with `Content-Security-Policy-Report-Only` first (header only, it does not work in `<meta>`), reporting via `report-to` plus a `Reporting-Endpoints` header; keep `report-uri` as fallback while browsers differ.
* `upgrade-insecure-requests` helps mixed content but does not replace HSTS.
* Frameworks: use the framework's nonce support (Django 6.0+ built-in CSP, Next.js and others per their docs) instead of hand-written headers.

## WebAssembly security notes
* Wasm runs inside the same browser sandbox and origin as JavaScript: memory-safe for the page, but bugs inside the module (buffer overflows in C or C++ compiled code) still corrupt its own linear memory and its outputs. Treat module output as untrusted input to the DOM.
* CSP: allow Wasm compilation with `'wasm-unsafe-eval'`, never with `'unsafe-eval'` (that also allows JS `eval`).
* Serve `.wasm` from your own origin with SRI or a fingerprinted name, `Content-Type: application/wasm`; a modified module owns the page as much as a modified script.
* Wasm 3.0 (completed in 2025) adds 64-bit memory, GC and exception handling; feature-detect before relying on them in older browsers.
* Secrets compiled into a module are as public as in JavaScript: binaries are easy to decompile.

## Exceptional conditions
* `fetch`: check `response.ok`, catch network errors, show a pt-BR message and a retry, never a raw error object or stack.
* A failed permission or auth check on the client only hides UI; the server must deny too.
* `window.onerror` and `unhandledrejection` reporting to the backend: send ids and messages, never form contents or tokens.

## Supply chain
* Scripts from a CDN carry `integrity` (SRI) and `crossorigin="anonymous"`; better, self-host and bundle them. A compromised third-party script owns the page.
* Tag managers and analytics run with full page access: keep them off login, payment and admin pages, or restrict them by CSP.
* Bundled dependencies follow the npm rules in `node-js.md` (lockfile, audit, install-script policy).

## Tuning
* Core Web Vitals targets at the 75th percentile: LCP 2.5 s or less, INP 200 ms or less, CLS 0.1 or less (web.dev/vitals). Measure with Lighthouse and field data before and after; report the number.
* Images: WebP or AVIF, `loading="lazy"` below the fold, explicit `width`/`height`, `srcset`; the LCP image is not lazy and may get `fetchpriority="high"`.
* Fonts self-hosted with `font-display: swap`. Critical CSS inline only when measured.
* Compression (gzip or Brotli); long `Cache-Control` only for fingerprinted files; HTML short-lived or `no-store` when personal.
* Animate `transform` and `opacity` only. Break long tasks so input stays responsive (INP).
* Follow the existing build pipeline; do not introduce a bundler into a site that has none.

## Traps and fixes
* `element.innerHTML = "<b>" + name + "</b>"`: XSS. Use `textContent` or create the `<b>` and set its text.
* `eval(json)` or `new Function` for parsing: `JSON.parse`.
* `<a href={userUrl}>` in a framework: frameworks escape text, not URL schemes. Validate the scheme.
* React `dangerouslySetInnerHTML`, Vue `v-html`, Angular `bypassSecurityTrust*` with API data: sanitize with DOMPurify or render text.
* CSP with `'unsafe-inline'` "temporarily": it disables the protection. Move inline code to files and add nonces.
* `div` with `onclick` as a button: not keyboard accessible. Use `<button>`.
* Placeholder as label: disappears on typing and fails accessibility. Visible `<label>`.

## Legacy front ends: safe maintenance
* jQuery or a pre-framework site that works: fix the reported fault, never rewrite. Update jQuery within its major first (old versions have known XSS in `$(html)` parsing), test, then consider the next major.
* Replace `.html(data)` calls with `.text(data)` file by file; move inline handlers to `addEventListener` before adding CSP, then roll CSP out in report-only mode.
