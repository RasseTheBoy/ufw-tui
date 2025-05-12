#!/usr/bin/env python3

import curses, subprocess, re
from typing import Literal, Optional
from curses import window


class Port:
    """A port object"""
    def __init__(
        self,
        port_num: str,
        allowed: bool,
        protocol: Literal['any', 'udp', 'tcp'] = 'any'
    ) -> None:
        self.port_num = port_num
        self.allowed = allowed
        self.protocol = protocol
    
    
    def str_port(self) -> str:
        if self.protocol == 'any':
            return self.port_num
        elif self.protocol == 'tcp' or self.protocol == 'udp':
            return f'{self.port_num}/{self.protocol}'
        else:
            raise ValueError(f'Invalid protocol: {self.protocol}')
    
        
    def allow(self) -> None:
        subprocess.run(['sudo', 'ufw', 'allow', self.str_port()])
        self.allowed = True
        
    
    def deny(self) -> None:
        subprocess.run(['sudo', 'ufw', 'deny', self.str_port()])
        self.allowed = False
    

    def delete(self) -> None:
        subprocess.run([
            'sudo', 'ufw', 'delete',
            'allow' if self.allowed else 'deny',
            self.str_port()
        ])


    def toggle(self) -> None:
        if self.allowed:
            self.deny()
        else:
            self.allow()


    def __repr__(self) -> str:
        return f'Port({self.port_num}, {self.allowed}, {self.protocol})'
    
    
    def str_allowed(self) -> str:
        return 'ALLOWED' if self.allowed else 'DENIED'



def get_ports() -> list[Port]:
    """Get a list of ports

    :raises ValueError: An error occured while getting the ports
    :raises ValueError: The amount of ports are not diviced by 2
    :return Port: A list of Port objects
    """
    result = subprocess.run(['sudo', 'ufw', 'status', 'numbered'], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    
    port_lst = []
    port_line_lst = [line for line in lines if re.match(r'^\[\s*(\d+)\]', line)]
    
    # Raise and error if the amount of ports are not diviced by 2
    if len(port_line_lst) % 2 != 0:
        raise ValueError('The amount of ports are not diviced by 2')
    
    # Cut the port_line_lst in half
    port_line_lst = port_line_lst[:len(port_line_lst) // 2]
    
    for line in port_line_lst:
        # Match groups:
        # 1: Port number
        # 2: Protocol
        # 3: ALLOW or DENY
        match = re.match(r'^\[\s*\d+\]\s+(\w+)(?:/(tcp|udp))?\s+(ALLOW|DENY)', line)
        
        if match is None:
            raise ValueError(f'Invalid line: {line}')
        
        port_num = match.group(1)
        protocol: Literal['any', 'udp', 'tcp'] = 'any' if match.group(2) is None else match.group(2)  # type: ignore
        allowed = match.group(3) == 'ALLOW'
        
        # Add the port to the list
        port_lst.append(Port(port_num, allowed, protocol))
        
    # Sort by port number
    port_lst.sort(key=lambda port: port.port_num)
        
    return port_lst


def input_window(stdscr: window, prompt: str) -> str:
    """Window for user input

    :param stdscr: Curses window
    :param prompt: Prompt to display
    :return str: User input
    """
    # Get the size of the screen
    h, w = stdscr.getmaxyx()
    win_h, win_w = 7, w - 4
    
    # Create a new window
    win = curses.newwin(win_h, win_w, h // 2 - win_h // 2, 2)
    win.box()
    win.addstr(1, 2, prompt)
    win.addstr(3, 2, '> ')
    curses.echo()
    win.refresh()
    
    # Get the input
    input_str = win.getstr(3, 4).decode('utf-8')
    curses.noecho()
    
    return input_str.strip()


def show_popup(
    stdscr: window,
    message: str,
    header: Optional[str] = None,
    width_ratio: float = 0.6,
    padding: int = 2
) -> None:
    """Show a popup window with a message

    :param stdscr: Curses window
    :param message: Message to display
    :param header: Header to display, defaults to None
    :param width_ratio: Window width ratio, defaults to 0.6
    :param padding: Padding, defaults to 2
    """
    h, w = stdscr.getmaxyx()
    lines = message.strip().split('\n')
    line_count = len(lines)

    # Adjust for header and space for footer
    extra_lines = 3 if header else 2
    win_h = line_count + extra_lines + padding
    win_w = int(w * width_ratio)
    win_y = max(0, (h - win_h) // 2)
    win_x = max(0, (w - win_w) // 2)

    win = curses.newwin(win_h, win_w, win_y, win_x)
    win.box()

    y = 1
    if header:
        centered_header = header.center(win_w - 4)
        win.addstr(y, 2, centered_header, curses.A_BOLD)
        y += 2  # Space between header and body

    for line in lines:
        if y >= win_h - 2:
            break
        win.addstr(y, 2, line[:win_w - 4])
        y += 1

    win.addstr(win_h - 1, 2, 'Press any key to continue...')
    win.refresh()
    win.getch()
    win.clear()
    stdscr.refresh()


def main(stdscr: window) -> None:
    """Main function

    :param stdscr: Curses window
    :raises ValueError: An error occured while getting the ports
    """
    curses.curs_set(0)
    
    port_lst = get_ports()
    current_index = 0
    
    while True:
        # Display the allowed ports
        stdscr.clear()
        stdscr.addstr(0, 0, 'UFW Port Manager — h to help, q to quit', curses.A_BOLD)
        
        if not port_lst:
            # Display a message if no ports are found
            stdscr.addstr(2, 0, 'No ports found (press "a" to add ports)')
        else:
            max_y, max_x = stdscr.getmaxyx()
            
            # Reserve top 2 lines for header
            visible_height = max_y - 2
            
            # Determine the scroll window
            start_index = max(
                0,
                current_index - visible_height + 1
            ) if current_index >= visible_height else 0
            end_index = min(len(port_lst), start_index + visible_height)

            # Display the ports and their status
            for visible_idx, actual_idx in enumerate(range(start_index, end_index)):
                port_obj = port_lst[actual_idx]
                attr = curses.A_REVERSE if actual_idx == current_index else 0
                stdscr.addstr(visible_idx + 2, 0, f'{port_obj.str_port().ljust(15)} {port_obj.str_allowed()}', attr)
        
        key_input = stdscr.getch()
        
        # Quit
        if key_input == ord('q'):
            break
        
        # Move selection up
        elif key_input == curses.KEY_UP and current_index > 0:
            current_index -= 1
        
        # Move selection down
        elif key_input == curses.KEY_DOWN and current_index < len(port_lst) - 1:
            current_index += 1
        
        # Toggle port
        elif key_input == ord(' '):
            if not port_lst:
                show_popup(stdscr, 'No ports to toggle', header='Error')
                continue
            
            # Toggle selectedd port
            port_lst[current_index].toggle()
        
        # Add new port(s)
        elif key_input == ord('a'):
            user_input = input_window(stdscr, 'Add new ports (spaces in between, `!` for denied): ')
            if not user_input:
                continue
            
            user_input_lst = user_input.split(' ')
            for port_input in user_input_lst:
                # Match groups:
                # 1: Denyed (!) or allowed (empty)
                # 2: Port number
                # 3: Protocol
                match = re.match(r'(!)?(\w+)(?:/(tcp|udp))?', port_input)
                if match is None:
                    show_popup(stdscr, f'Invalid port: {port_input}')
                    continue
                
                port = Port(
                    port_num=match.group(2),
                    allowed=match.group(1) != '!',
                    protocol=match.group(3) or 'any'  # type: ignore
                )
                
                # Skip port if it already existst
                if port.port_num in [port.port_num for port in port_lst]:
                    show_popup(stdscr, f'Port {port.port_num} already exists')
                    continue
                
                if port.allowed:
                    port.allow()
                else:
                    port.deny()
                    
                port_lst.append(port)

        # Delete port
        elif key_input == ord('d'):
            port_lst[current_index].delete()
            port_lst.pop(current_index)
            
            # If the current index is out of bounds, set it to the last index
            if current_index >= len(port_lst):
                current_index = len(port_lst) - 1
        
        # Help winodw
        elif key_input == ord('h'):
            show_popup(
                stdscr,
                header='Help',
                message=(
                    '↑ / ↓  : Navigate\n'
                    'SPACE  : Toggle selected port\n'
                    'a      : Add new (allowed) ports\n'
                    'd      : Delete selected port\n'
                    'q      : Quit'
                )
            )
        
        stdscr.refresh()


if __name__ == '__main__':
    curses.wrapper(main)
