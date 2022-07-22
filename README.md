# circdeploy

## Easily deploy your CircuitPython projects

Deploys the current working directory to a connected CircuitPython device.

I don't like editing CircuitPython files directly from the mounted device folder. The OS may be
creating hidden files or your IDE may be saving files frequently which may trigger the device
to reboot.

**Default behavior:** Copies all `./**/*.py` and `./**/*.pyc` files from the current directory to an
automatically detected CircuitPython device, skipping any files in `.gitignore`

```shell
$ circdeploy --help

 Usage: circdeploy [OPTIONS]

 Deploy current CircuitPython project

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --source,--src        -s                    TEXT  Deploy from this location. [default: (current working directory)]                     │
│ --destination,--dest  -d                    TEXT  Deploy to this location. [default: (device path automatically detected)]              │
│ --use-gitignore           --no-gitignore          Ignore files using .gitignore files relative to source path. [default: use-gitignore] │
│ --dry-run                                         Don't copy files, only output what would be done.                                     │
│ --install-completion                              Install completion for the current shell.                                             │
│ --show-completion                                 Show completion for the current shell, to copy it or customize the installation.      │
│ --help                                            Show this message and exit.                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
