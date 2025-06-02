git clone https://www.github.com/odoo/odoo --depth 1 --branch 12.0 /opt/odoo12/odoo
cd /opt/odoo12
python3 -m venv odoo-venv
source odoo-venv/bin/activate
pip3 install wheel
pip3 install -r odoo/requirements.txt
deactivate
mkdir /opt/odoo12/custom
exit
psql
sudo postgres
sudo su
exit
