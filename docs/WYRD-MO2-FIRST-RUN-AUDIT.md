# Wyrd MO2 First-Run Behavior Audit

## Findings

- MO2's `--pick` option forces the instance selection dialog at startup.
- MO2's `-i <instanceName>` option selects a named instance. An empty instance name has historically been discussed as portable-instance selection, but behavior and support are version-sensitive; Wyrd must not rely on it without testing against the exact MO2 release.
- MO2's current first-run wizard is the supported path for creating an instance. It asks the user to select instance type, game, profile settings, and data locations.
- A portable instance stores its data under the MO2 installation folder; a global instance stores data separately. Wyrd should favor a portable instance inside its owned MO2 install only if that is validated and safe.
- MO2 instances contain user data (mods, downloads, profiles, overwrite, configuration). Wyrd must never create, overwrite, or delete instance folders without explicit ownership and validation.

## Wyrd's current behavior

Wyrd launches MO2 normally for a first-time setup and uses `--pick` to show the instance picker when no instance is detected. The user creates a Skyrim Special Edition instance through MO2's wizard.

## Automation decision

Do not attempt to synthesize MO2 instance configuration files or invoke undocumented instance-creation flags. Automating instance creation should wait until Wyrd has validated the official MO2 configuration schema and the Skyrim game plugin's discovery requirements against a real Proton prefix. For now, keep the official wizard and clearly explain the steps in Wyrd's GUI.

## References

- MO2 upstream command line source: https://github.com/ModOrganizer2/modorganizer/blob/master/src/commandline.cpp
- MO2 upstream instance dialog: https://github.com/ModOrganizer2/modorganizer/blob/master/src/instancemanagerdialog.cpp
- MO2 instance creation guidance: https://github.com/ModOrganizer2/modorganizer/wiki/Instances
