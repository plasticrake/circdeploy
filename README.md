# circdeploy

## Easily deploy your CircuitPython projects

Deploys the current working directory to a connected CircuitPython device.

I don't like editing CircuitPython files directly from the mounted device folder. The OS may be
creating hidden files or your IDE may be saving files frequently which may trigger the device
to reboot.

**Default behavior:** Copies all `./**/*.py` and `./**/*.pyc` files from the current directory to an
automatically detected CircuitPython device, skipping any files in `.gitignore`. Any remaining
`./**/*.py` and `./**/*.pyc` files on the device are deleted (`./lib/*` is not deleted).

### File Cache

By default, a file cache is used to only copy files that have been changed in the source directory.
If a file was changed manually in the destination, or if the destination is different than a
previous deploy, then not all files may be copied. You can disable the cache check with
`--no-cache`, or reset the cache for that source with `--reset-cache`.

###

```text
$ circdeploy --help

Usage: circdeploy [OPTIONS]                                                                                                               
                                                                                                                                           
 Deploy current CircuitPython project                                                                                                      
                                                                                                                                           
 All .py and .pyc files in the current directory tree will be copied to the destination (device)                                           
 All other .py and .pyc files in the destination directory tree (device) will be deleted except /lib/ (disable with --no-delete)           
                                                                                                                                           
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --source,--src        -s                    TEXT  Deploy from this location. [default: (Current working directory)]                     │
│ --destination,--dest  -d                    TEXT  Deploy to this location. [default: (Device path automatically detected)]              │
│ --delete                  --no-delete             Delete files in destination. [default: delete]                                        │
│ --use-gitignore           --no-gitignore          Ignore files using .gitignore files relative to source path. [default: use-gitignore] │
│ --use-cache               --no-cache              Use file cache to skip unchanged files. [default: use-cache]                          │
│ --reset-cache                                     Reset file cache.                                                                     │
│ --dry-run                                         Don't copy files, only output what would be done.                                     │
│ --install-completion                              Install completion for the current shell.                                             │
│ --show-completion                                 Show completion for the current shell, to copy it or customize the installation.      │
│ --help                                            Show this message and exit.                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
