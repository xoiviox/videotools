import threading, sys, os
from videotools import app, socketio
from videotools.utils import monitor_changes


if __name__ == '__main__':
    # import logging
    # logging.getLogger('werkzeug').setLevel(logging.ERROR)

    try:
        threading.Thread(target=monitor_changes, daemon=True).start()
        threading.Thread(target=socketio.run(app, debug=False, host='0.0.0.0', port=9999), daemon=False).start()
        print()
        
    except KeyboardInterrupt:
        try:
            print()
            sys.exit(1)
        except SystemExit:
            print()
            os._exit(1)
