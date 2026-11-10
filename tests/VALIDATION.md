# v1.7 validation

Executed `FROSTY_MOBILE_ENGINE=chromium python3 tests/smoke.py` successfully.

- Desktop Chromium, 1440 × 900: PASS.
- iPhone 13 profile, Chromium mobile emulation with touch: PASS.
- Both characters start; menu, settings, pause/resume, keyboard/swipe movement,
  manual landing/jump, automatic jump, booster impulse, coin collection,
  mute and volume persistence: PASS.
- No JavaScript page errors or failed HTTP asset responses.
- PNG decoder verifies actual alpha transparency in all three platform sprites.
- Screenshots visually reviewed on desktop and iPhone profile: no blue platform
  rectangles; central baked-in floating rocks removed; detailed winter scenery retained.
- `git diff --check`: PASS.

Safari/WebKit was NOT executed: Playwright browser download was denied with
HTTP 403 Domain forbidden for cdn.playwright.dev and
playwright.download.prss.microsoft.com. Run the default test command after
installing WebKit on a machine with permitted download access.
Actual iPhone hardware, tilt sensors and physical sound output remain untested.
The production physics, coin, booster and audio logic were kept unchanged.

The test injects private observation/scenario hooks into its own intercepted
HTTP response only; the shipped game has no debug API. Screenshots default to
/tmp/frosty-v1.7-tests, configurable with FROSTY_TEST_ARTIFACTS.
