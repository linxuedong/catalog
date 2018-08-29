Place your catalog project in this directory.

## Work with venv
```
python3 -m venv venv
source venv/bin/activate
```

## Install
```
pip install -r requirements.txt
```

## Database
```
# create database
sudo -i -u postgres
createdb -O vagrant catalog

# init db
python -m sqla_yaml_fixtures --db-url postgresql://vagrant@localhost/catalog --db-base catalog.models:Base --reset-db catalog/sample.yaml
```

## Run Application
```
cd /vagrant
export FLASK_APP=catalog
export FLASK_ENV=development

flsak run --host 0.0.0.0
```
