# UI Prototype

Use the existing app context when it helps judge real hierarchy, density, and interaction. Preserve its component system, navigation assumptions, and relevant states; use identified fixtures when live data is unnecessary.

1. Match the request. A specified layout or single prototype gets one version. When the user wants alternatives, choose two or three meaningfully different layouts or flows unless they specified a count. Do not add variants that differ only in color or wording.
2. Prefer an existing dev preview or experimental route. If mounting on an existing page, gate the entire experimental rendering branch from production, not just its controls. Preserve the normal route and relevant auth/data boundaries. A new route is appropriate when no existing surface fits.
3. Make the decisive interaction work. Include meaningful empty, invalid, loading, or dense-data states when those affect the design question. Stub mutations unless real effects are authorized.
4. Add a switcher only when comparing variants. Reuse native buttons or existing controls; URL parameters are useful for shareable states but not mandatory. Keep controls keyboard accessible and avoid intercepting input/navigation keys. A floating bar or shared switcher abstraction is unnecessary for one design.
5. Run the page in the intended viewport and exercise the key interaction in a real browser when available. Check readability, focus, overflow, and the relevant failure state. Record unavailable browser verification honestly and provide the runnable URL/command.
6. Hand over the artifact and the design tradeoff it exposes. After the user chooses a direction and authorizes integration, remove losing variants and prototype controls; retain useful code with production validation and error handling.

The prototype should look and behave well enough to decide the question. Avoid decorative work or infrastructure that does not contribute to that decision.
