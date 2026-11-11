FROSTY – Endless Ice Jump v1.7

Local play:
  python3 -m http.server 8000
Open the server root in your browser; index.html opens FROSTY_v1_7_index.html.
No build, runtime packages, API keys or backend are required.

Controls: default swipe/drag; select Pfeiltasten in settings for desktop arrows.
Space jumps in manual mode. Touch and tilt, Frosty/Lunar, auto/manual jump,
coins, boosters, music, volume and saved settings are retained.

Validation (Python Playwright and Chromium required):
  python3 tests/smoke.py
Install test tools if absent: python3 -m pip install playwright
Then: python3 -m playwright install chromium webkit
The suite serves its own local HTTP server and tests desktop Chromium and
an iPhone viewport with touch in WebKit. Device emulation does not validate
physical tilt sensors, iOS audio output or actual iPhone hardware.
If WebKit cannot be installed, run the explicit Chromium mobile fallback:
  FROSTY_MOBILE_ENGINE=chromium python3 tests/smoke.py
This fallback is not a Safari test.

GitHub Pages, only AFTER reviewing and approving the pull request:
1. Merge the approved branch into main.
2. In repository Settings > Pages choose Deploy from a branch, main, / (root).
3. Save and wait for the Pages deployment to finish.
4. Open https://oyamakuro.github.io/frosty-endless-jump/ .
To test the branch before merging, check it out locally and use the local server.
Do not switch the production Pages source to the review branch.

Graphics: alpha-transparent platform sprites and a continuous winter background
without the three central floating islands. Background variants share the same
clean illustration. Asset query versions are v1.7 to refresh prior cached images.
