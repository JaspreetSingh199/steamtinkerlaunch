# STL-Steam Qt6 desktop UI

Run the application:

```bash
bash qt-ui/run.sh
```

Install the desktop launcher:

```bash
bash qt-ui/install-desktop-launcher.sh
```

The current prototype performs read-only Steam, Skyrim, MO2 and STL detection.
It does not edit Steam's `localconfig.vdf`, change launch options, alter a Proton
prefix, or migrate an MO2 instance. Skyrim SE is AppID `489830`.

For Proton games, upstream SteamTinkerLaunch documents installation as a Steam
Compatibility Tool as the intended integration. The launch-option form
`steamtinkerlaunch %command%` is intended for native Linux games; do not apply
it blindly to Skyrim SE.
