# Harnaś

Harnaś (pol. kind of highlander) - system meant to be used by educational institutions, which focues on automated checking of programming assigments. We want to provide easy to use, highly configurable environment, which can handle different technologies from C++ through SQL to CUDA.

## Technologies

- [Hera](https://github.com/zielmicha/hera) - sandbox used to protect against malicious users.

## Setting up

Create virtual environment (for example using `virtualenv-wrapper`) and install dependencies:

```
mkvirtualenv -p /usr/bin/python3.4 venv
pip install -r requirements.txt
```

Copy settings and customize:

```
cp local_settings.py.example local_settings.py
```


Set up the database:

```
./manage.py migrate
```

Create superuser:

```
./manage.py createsuperuser
```
