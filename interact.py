import os
import sys
import wcwidth
import msvcrt

import event


class ScrollView(event.EventTarget):
    option_index = 0
    options_offset = 0

    def go_up(self):
        self.option_index = (self.option_index - 1 + len(self.options)) % len(self.options)
        if self.option_index < self.options_offset:
            self.options_offset = self.option_index
        elif self.option_index >= self.options_offset + os.get_terminal_size().lines - 2:
            self.options_offset = self.option_index - os.get_terminal_size().lines + 2

    def go_down(self):
        self.option_index = (self.option_index + 1) % len(self.options)
        if self.option_index >= self.options_offset + os.get_terminal_size().lines - 2:
            self.options_offset = self.option_index - os.get_terminal_size().lines + 2
        elif self.option_index < self.options_offset:
            self.options_offset = self.option_index
        
    def hide(self):
        self.displayed = False
        self.condition = False
        sys.stdout.write('\033[2J\033[0;0H\033[?25h\033[0m')

    @staticmethod
    def get_columns(text):
        return sum([wcwidth.wcwidth(c) for c in text])

    @staticmethod
    def line_handler(line, width = None):
        if width is None:
            width = os.get_terminal_size().columns + len(line) - ScrollView.get_columns(line)
        if ScrollView.get_columns(line) > os.get_terminal_size().columns:
            return line[:width - 3] + '...'
        return line
    
    @staticmethod
    def get_text_args(text, origin_width):
        return origin_width - len(text) + ScrollView.get_columns(text), text
    
    def show(self):
        sys.stdout.write('\033[2J\033[?25l')
        self.displayed = True
        self.condition = True
        while self.condition:
            if self.paused:
                continue
            try:
                sys.stdout.write('\033[0;0H')
                for index, option in [* enumerate(self.options)][self.options_offset:self.options_offset + os.get_terminal_size().lines - 1]:
                    is_cur_line = self.option_index == index
                    sys.stdout.write('\033[46m\033[1;37m' if is_cur_line else '\033[2;37m')
                    sys.stdout.write('%s\n' % self.line_handler(self.item_text({
                        'is_cur_line': is_cur_line, 
                        'title': option
                    })))
                    sys.stdout.write('\033[0m')

                sys.stdout.write('%*s' % ScrollView.get_text_args(ScrollView.line_handler(self.bottom_text({
                    'index': self.option_index, 
                    'title': self.options[self.option_index]
                })), - os.get_terminal_size().columns))

                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if ch == b'\xe0':
                        ch = ch + msvcrt.getch()
                        {
                            b'\xe0\x48': self.go_up, 
                            b'\xe0\x50': self.go_down
                        }.get(ch, lambda : 0)()
                    self.dispatchEvent(event.Event('key-input', { 'detail': { 'char': ch } }))
            except KeyboardInterrupt:
                break
        self.hide()

    def __init__(self, options = [], 
                 item_text = lambda conf: '%s%*s%s' % (
                     '[ ' if conf['is_cur_line'] else '  ', 
                     * ScrollView.get_text_args(ScrollView.line_handler(conf['title'], os.get_terminal_size().columns - 4 - ScrollView.get_columns(conf['title']) + len(conf['title'])), - os.get_terminal_size().columns + 4), 
                     ' ]' if conf['is_cur_line'] else '  '), 
                 bottom_text = lambda conf: '[{index}] {title}'.format(**conf), 
                 immediate = True):
        self.options = options
        self.item_text = item_text
        self.bottom_text = bottom_text
        self.displayed = False
        self.paused = False
        if immediate:
            self.show()

