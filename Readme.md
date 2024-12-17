
# Django Project Setup

This guide will help you set up and run the Django project locally.

## Prerequisites

Before you begin, ensure you have the following installed on your machine:

- Python (3.6+)
- pip (Python package installer)
- virtualenv (optional but recommended)
- PostgreSQL (or your preferred database)

## Setup Instructions

```bash
brew install pyenv
nano ~/.zshrc
```

```bash
# Pyenv setup 
if command -v pyenv 1>/dev/null 2>&1; then
  export PYENV_ROOT="$HOME/.pyenv"
  [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init -)"
fi
```

```bash
pyenv install 3.10.16
pyenv global 3.10.15
brew install pyenv-virtualenv
pyenv virtualenv 3.10.16 myenv
pyenv activate myenv
# Set the local python version to the virtualenv
pyenv local myenv 
```

From then on you can just run
```pyenv activate```

Now install the required packages:
```pip install -r requirements.txt```

```bash
brew install gdal
brew install geos 
brew install postgresql postgis
brew install fontconfig
```

Create a .env file with all the variables
```bash
cd clinks
export $(cat .env | xargs)
```

Check migrations
```bash
python manage.py showmigration
python manage.py migrate api --fake
python manage.py makemigrations
python manage.py migrate 
```
