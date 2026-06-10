Usage example of the script in VSCode `tasks.json` file
This example requires using `CodeLLDB (vadimcn.vscode-lldb)` and `Tasks Shell Input (augustocdias.tasks-shell-input)` extensions 

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Android debug",
            "type": "lldb",
            "request": "attach",
            "pid": "${input:pid}",
            "initCommands": [
                "platform select remote-android",
                "platform connect unix-abstract-connect:///my-debug-socket",

                "settings set plugin.jit-loader.gdb.enable off",

                "settings append target.exec-search-paths \"/home/user/Desktop/my-cool-app/build\""
            ],
            "postRunCommands": [
                "process handle SIGCHLD --pass true --stop false --notify false",
                "command script import /path/to/ignore_android_exceptions.py",
            ]
        }
    ],
    "inputs": [
        {
            "id": "pid",
            "type": "command",
            "command": "shellCommand.execute",
            "args": {
                "command": "adb shell pidof com.my.app",
                "useFirstResult": true
            }
        }
    ]
}

```