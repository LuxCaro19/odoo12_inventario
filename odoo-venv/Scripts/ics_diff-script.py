#!c:\opt\odoo12\odoo-venv\scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'vobject==0.9.3','console_scripts','ics_diff'
__requires__ = 'vobject==0.9.3'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('vobject==0.9.3', 'console_scripts', 'ics_diff')()
    )
