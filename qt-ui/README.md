# STL-Steam Qt6 desktop UI

Run the application:

```bash
bash qt-ui/run.sh
```

Install the desktop launcher:

```bash
bash qt-ui/install-desktop-launcher.sh
```

The app performs read-only Steam, Skyrim, and MO2 detection. The Compatibility
page can install upstream SteamTinkerLaunch by cloning it into the user-local
`~/stl/prefix` directory when missing, then runs STL's supported
`steamtinkerlaunch compat add` command to register it with Steam. Existing
compatibility-tool targets are never overwritten. The app does not edit Steam's
`localconfig.vdf`, change launch options, alter a Proton prefix, or migrate an
MO2 instance. Skyrim SE is AppID `489830`.

For Proton games, upstream SteamTinkerLaunch documents installation as a Steam
Compatibility Tool as the intended integration. The launch-option form
`steamtinkerlaunch %command%` is intended for native Linux games; do not apply
it blindly to Skyrim SE.
