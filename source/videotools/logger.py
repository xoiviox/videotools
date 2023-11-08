from datetime import datetime
from videotools import socketio
from videotools.config import DirConfig, OtherConfig


def logg(level, msg1,  msg2 = ''):
    if OtherConfig.log_web_level >= level:
        web_msg = f'{str(datetime.now())[:-3]}: {msg1}'
        web_msg = web_msg + ' ' + str(msg2)
        socketio.emit('logger_update', web_msg)
    if OtherConfig.log_print_level >= level:
        print_msg = f'{str(datetime.now())[:-3]}: {msg1}'
        if len(print_msg) <= OtherConfig.log_gap:
            needed_spaces = OtherConfig.log_gap - len(print_msg)
            print_msg = print_msg + (needed_spaces * ' ') + str(msg2)
        else:
            print_msg = print_msg + msg2
        print(print_msg)
    if OtherConfig.log_write_level >= level:
        write_msg = f'{str(datetime.now())[:-6]}: {level}: {msg1}'
        if len(write_msg) <= OtherConfig.log_gap + 4:
            needed_spaces = OtherConfig.log_gap + 4 - len(write_msg)
            write_msg = write_msg + (needed_spaces * ' ') + str(msg2)
        else:
            write_msg = write_msg + msg2
        try:
            with open(f'{DirConfig.d_conf}log.txt', 'a') as logfile:
                logfile.write(write_msg + '\n')
        except:
            logg(5, '=' * 175 + ' error writting to log file')

