# Mise Browser

A lightweight, distraction-free, keyboard-driven terminal companion browser built with Python, PyQt6, and QtWebEngine. Mise bridges the gap between terminal efficiency and the modern web, offering independent workspace isolation, persistent session workflows, and strict asset blocking without the bulk of traditional browsers.

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

## Directory Layout

```zsh
~/.config/mise/
├── session.json                # Serialised workspace layout states
└── browser_profile/            # Isolated cookie jars and disk cache profiles
```
---

## Core Component Control Mappings
**Global Keyboard Actions**

| Key Binding | Scope Context | Target Execution Logic |
|---|---|---|
| Ctrl + T | Application | Spawns a fresh tab instance routed to default search engine. |
| Ctrl + W | Browser View | Close the active browser view widget container securely. |
| Ctrl + B | Application | Focus directly into the webview window. |
| Ctrl + Shift + W | Application | Toggles between active workspace tabs and the Workspaces Dashboard. |
| Ctrl + S | Browser View | Clones the current address layout directly into a new duplicate tab. |
| Ctrl + R | Browser View | Sends an immediate reload instruction wrapper to the active web page. |
| Ctrl + D | Dashboard Tree | Quick-remove macro to clear the focused element item from memory. |
| Ctrl + L | Application | Activates the floating wide address input box overlay spanning the frame. |
| Ctrl + M | Application | Focus directly into the sidebar panel for instant arrow handling. |
| CTRL + F | Application | Toggle links hints overlay. |
| CTRL + P | Application | Opens a command palette floating window. |

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
