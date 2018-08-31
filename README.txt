# The IP address and SSH port so your server can be accessed by the reviewer.
IP: 52.194.187.198
Port: 2200


# Web application URL:
[Catalog](http://52.194.187.198/)


# A summary of software you installed and configuration changes made.
### Login
```
chmod 400 catalog.pem
ssh -i catalog.pem ubuntu@13.231.128.179
```

### Update all currently installed packages.

```
sudo apt-get update
```
[自动更新](https://help.ubuntu.com/lts/serverguide/automatic-updates.html)
[amazon ec2 - Update Ubuntu 10.04 - Server Fault](https://serverfault.com/questions/262751/update-ubuntu-10-04/262773#262773)

### Change the SSH port from 22 to 2200. Make sure to configure the Lightsail firewall to allow it.

```
ubuntu@ip-172-26-8-100:~$ sudo ufw status
Status: inactive
ubuntu@ip-172-26-8-100:~$ sudo ufw default deny incoming
Default incoming policy changed to 'deny'
(be sure to update your rules accordingly)
ubuntu@ip-172-26-8-100:~$ sudo ufw status
Status: inactive
ubuntu@ip-172-26-8-100:~$ sudo ufw default allow outgoing
Default outgoing policy changed to 'allow'
(be sure to update your rules accordingly)
ubuntu@ip-172-26-8-100:~$ sudo ufw status

```

### Configure the Uncomplicated Firewall (UFW) to only allow incoming connections for SSH (port 2200), HTTP (port 80), and NTP (port 123).

```
sudo ufw allow 2200
sudo ufw allow www
sudo ufw allow 123
sudo ufw enable
sudo ufw status
```
`sudo ufw status` 返回结果

```
Status: active

To                         Action      From
--                         ------      ----
22                         ALLOW       Anywhere
2200/tcp                   ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
123                        ALLOW       Anywhere
22 (v6)                    ALLOW       Anywhere (v6)
2200/tcp (v6)              ALLOW       Anywhere (v6)
80/tcp (v6)                ALLOW       Anywhere (v6)
123 (v6)                   ALLOW       Anywhere (v6)
```

### Create a new user account named grader.

```
sudo adduser garder

# check
finger garder
```

### Give grader the permission to sudo.

```
sudo cp /etc/sudoers.d/90-cloud-init-users /etc/sudoers.d/garder
sudo nano /etc/sudoers.d/garder
```

/etc/sudoers.d/garder
```
garder ALL=(ALL) NOPASSWD:ALL
```

```
sudo vim /etc/ssh/sshd_config

# edit file
PermitRootLogin no
```

### Create an SSH key pair for grader using the ssh-keygen tool.

```
sudo -i -u garder
ssh-keygen

touch authorized_keys
vim authorized_keys
```
Then add id_rsa.pub content into authorized_keys


## Prepare to deploy your project.

### Configure the local timezone to UTC.

```
# 查看
date
timedatectl --no-pager list-timezones
sudo timedatectl set-timezone Asia/Shanghai
```

```
$ timedatectl
      Local time: Wed 2018-08-29 12:18:23 CST
  Universal time: Wed 2018-08-29 04:18:23 UTC
        RTC time: Wed 2018-08-29 04:18:23
       Time zone: Asia/Shanghai (CST, +0800)
 Network time on: yes
NTP synchronized: yes
 RTC in local TZ: no
```


### Install and configure Apache to serve a Python mod_wsgi application.

```
sudo apt-get install apache2

```

### Install and configure PostgreSQL:

```
sudo apt-get install postgresql
sudo -i -u postgres
createuser catalog
createdb -O catalog catalog
```

### Install git.

Already have.
```
cd /var/www
sudo mkdir catalog
sudo chmod 777 catalog
git clone https://github.com/linxuedong/catalog.git
```

virtualenv
```
sudo apt-get install virtualenvwrapper
. /etc/bash_completion.d/virtualenvwrapper
mkvirtualenv catalog --python=/usr/bin/python3.5
workon catalog
pip install -r catalog/requirements.txt
```

### Install and configure Nginx to serve a Python Gunicorn application.

```
sudo apt-get install nginx
sudo service nginx start

touch nginx.conf
vim nginx.conf
```

The nginx.conf content
```
server {
    listen       80;
    server_name  52.83.166.174;

    location / {
        proxy_pass http://127.0.0.1:8080;
    }
}
```

Then restart nginx

```
sudo ln -s /var/www/catalog/nginx.conf /etc/nginx/sites-enabled/
sudo service nginx restart
```

Run gunicorn
```
cd /var/www/
gunicorn -w 4 -b 127.0.0.1:5000 catalog:app
```

# Question
I want to running gunicorn as service, but it was not work!

```
sudo nano /etc/init/catalog.conf
```

catalog.conf
```
description "The catalog service"

start on runlevel [2345]
stop on runlevel [!2345]


respawn
setuid root
setgid www-data

env PATH= /home/ubuntu/.virtualenvs/venv/bin
chdir /var/www/

exec gunicorn -w 4 -b 127.0.0.1:5000 catalog:app
```


# A list of any third-party resources you made use of to complete this project.
[使用 SSH 连接到 Linux 实例 - Amazon Elastic Compute Cloud](https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html)

[ssh "permissions are too open" error - Stack Overflow](https://stackoverflow.com/questions/9270734/ssh-permissions-are-too-open-error)

[How To Set Timezone and NTP Sync on Ubuntu [Quickstart] | DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-set-up-timezone-and-ntp-synchronization-on-ubuntu-14-04-quickstart)

[Flask + Gunicorn + Nginx 部署 - Ray Liang - 博客园](https://www.cnblogs.com/Ray-liang/p/4837850.html)
