```shell

git clone https://github.com/primal100/CryptoVPN.git

pip install -r requirements.txt

python manage.py makemigrations

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver

```

Open:
http://localhost:8000

From a client side perspective, the following directories are the most important:
 
HTML: cryptovpnapp/templates/cryptovpnapp

CSS/JS: cryptovpn/static/cryptovpn