# Mise Browser

Mise is a minimalist, keyboard-driven browser built with Python and QtWebEngine. It is designed specifically for power users who want maximum performance and zero interface clutter, making it ideal for fanless or resource-constrained laptops.

## Key Features
- **Workspace Isolation**: Separate tab configurations into independent context layers, dynamically hydrating browser instances on demand to save memory.
- **Persistent Authentication**: Dedicated, isolated cookie profile storage saves session tokens and logins securely to disk across restarts.
- **Keyboard-Centric Navigation**: Native workflow controls for fluid tab switching, address overrides, and workspace cycling with standard arrow loops without dropping context.
- **Hardcoded Palette Modding**: Zero file-watcher lag. Adjust light and dark hex structures directly from a single style configuration file.
- **Telemetry & Noise Interception**: Low-level process filters drop trackers, data-logging calls, and canvas tracking requests at the engine layout level.

---

## Installation & Deployment
**Clone the repository directly from GitHub into your local projects directory and run the application initialization sequence**:

**Clone the workspace repository**

`git clone https://github.com/Rakosn1cek/Mise.git`

**Navigate into the project root directory**

`cd Mise`

**Launch the browser interface instance**

`python3 mise.py`

---

## Core Design
- Built on a Chromium backbone via QtWebEngine without the usual browser overhead.
- Distro-agnostic architecture running completely within local user space.
- Native network-level ad and telemetry blocking that drops tracking requests before they download, keeping CPU utilisation low.
- Aggressive background tab throttling profiles to prevent thermal spikes on fanless hardware.
- Dynamic workspace layout separation to switch between tasks instantly.

---

## Repository Structure
- mise.py: The main application entry point and engine initialization loop.
- workspace.py: Layout management, session handling, and the workspace dashboard tree [cite: 2026-07-04].
- blocker.py: C++ level network request interceptor for bloat-free telemetry blocking.
- config.py: Local JSON hardware configuration profiles and settings interface.
- palette.py: Keyboard-driven command palette for interface navigation.
- theme.py: Central stylesheet definitions handling dynamic dark and light mode shifts.
- help-menu.py: Keybind reference and documentation overlay.
- permissions.py: Granular site permission handling and rule sets.
- notification-worker.py: Low-overhead background notification subsystem.
- hinter.js: Injected script handler for link hinting and keyboard navigation.

---

## Core Component Control Mappings
**Global Keyboard Actions**

| Key Binding | Scope Context | Target Execution Logic |
| Ctrl + T | Application | Spawns a fresh tab instance routed to default search engine. |
| Ctrl + W | Browser View | Close the active browser view widget container securely. |
| Ctrl + B | Aplictaion | Focus directly into the webview window. |
| Ctrl + Shift + W | Application | Toggles between active workspace tabs and the Workspaces Dashboard. |
| Ctrl + S | Browser View | Clones the current address layout directly into a new duplicate tab. |
| Ctrl + R | Browser View | Sends an immediate reload instruction wrapper to the active web page. |
| Ctrl + D | Dashboard Tree | Quick-remove macro to clear the focused element item from memory. |
| Ctrl + L | Application | Activates the floating wide address input box overlay spanning the frame. |
| Ctrl + M | Application | Focus directly into the sidebar panel for instant arrow handling. |
| CTRL + F | Aplication | Toggle links hints overlay. |
| CTRL + P | Aplicattion | Opens a command palette floating window. |

---

## Interface Interaction Signals
- **Sidebar Arrow Tuning**: Moving Up or Down arrows inside the sidebar switches active web pages instantly without forcing keyboard focus away from the navigation list.
- **Dashboard Context Peeking**: Moving the selection ring over Workspace items inside the dashboard tree automatically mounts and links backend parameters, updating state tracking labels without dropping tree focus.
- **Committing Context Changes**: Pressing Enter, Return, or trigger double clicks over active nodes loads the targeted layout view and closes the dashboard.
- **Theme Selection Button**: Located at the lower base of the sidebar frame. Triggers dynamic interface palette repainting across elements and switches Chromium rendering attributes without rebooting application pipelines.

---

## Engine Input Parsing Architecture
Address commitments executed inside the wide address bar are structured through a multi-tier parsing routine to separate search statements from physical local or external endpoints:

1. Space Isolation: Input strings matching whitespace divisions are packed as multi-word queries and routed directly to DuckDuckGo search strings.
2. Explicit Scheme Trapping: Strings initiating with http:// or https:// are processed directly to bypass fallback inspection routines.
3. Local Node Matching: Isolates the host block before any subdirectory chains to identify internal address ranges (192.168.x.x, 10.x.x.x, 127.0.x.x) or local loop labels (localhost, router, gateway), deploying direct target handoffs cleanly.
4. TLD Validation: Inspects targeted domain tags for matching extensions (.com, .org, .net, .cz, .uk, .moe, .local, .lan). If detected, it initiates standard secure lookup pathways; otherwise, unstructured phrases fall back safely into the search queue.

---

## Dependencies & Run Execution
Mise requires an environment tracking modern Python bindings alongside system database frameworks:

**Required Packages (Arch Linux Reference)**

`sudo pacman -S python-pyqt6 python-pyqt6-webengine`

**Direct Invocation Trace**

`python3 mise.py`

All session data and hardware optimization profiles persist cleanly inside ~/.config/mise/. 

Contributions, code audits, and optimizations regarding resource reduction are welcome.
