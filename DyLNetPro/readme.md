# Dylnet flask app.

### lancer l'appli
`python3.8 app_base.py`

l'application sera disponible à `localhost:5000`

### conf apache pour lier ça à un nom de domaine
```
<VirtualHost *:80>
ServerName flask.test
ProxyPreserveHost On
ProxyPass / http://localhost:5000/
ProxyPassReverse / http://localhost:5000/
Timeout 2400
ProxyTimeout 2400
</VirtualHost>
```

### utilisation en tant que service
création d'un fichier `/lib/systemd/system/flask.service`

```
[Unit]
Description=Flask web server
After=network.target

[Install]
WantedBy=multi-user.target

[Service]
User=fagotju
WorkingDirectory=/home/fagotju/Flask
ExecStart=/usr/bin/python3 /home/fagotju/Flask/app_base.py
TimeoutSec=600
Restart=always
```

```
sudo systemctl enable flask.service
sudo systemctl start flask.service
sudo systemctl status flask.service
```

### Contributions
* Aurélie Nardy
* Isabelle Rousset
* Arnaud Bey
* Julien Fagot
* Sylvain Hatier
* Youssef Hamrouni
* Rachel Gaubil
