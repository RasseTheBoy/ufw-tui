# UFW-TUI

UFW-TUI (Uncomplicated Firewall-Text User Interface) is a simple command-line tool for managing UFW rules.

## Installation

1. Download the python script.
2. Make it executable: `chmod +x ufw-tui.py`
3. Move to a directory in your PATH, e.g. `/usr/local/bin`: `sudo mv ufw_tui.py /usr/local/bin/ufw-tui`
4. (Optional) Create a symbolic link: `sudo ln -s /path/to/file/ufw_tui.py /usr/local/bin/ufw-tui`
5. Run it: `ufw-tui`

## Usage

| Key | Action |
| --- | --- |
| a | Add new rules |
| ↑ / ↓ | Navigate the list of rules |
| SPACE | Toggle the rule state (ALLOW / DENY) |
| d | Delete the selected rule |
| q | Quit the program |
| h | Show a help screen |

## Adding new rules

To add a new rule, press the `a` key. 
A new window will open where you can write the rules with a space between.\
Ports that are already in use will not be added.

### Allow

Just write the ports you want to allow.

```
> 8080 8081/udp 8082/tcp 8083
```

This would allow  port 8080, 8081/udp, 8082/tcp and 8083.

### Deny

Add a `!` before the ports you want to deny.

```
> !8080 8081/udp !8082/tcp 8083
```

This would deny port 8080 and 8083, but allow 8081/udp and 8082/tcp.