FROM python:3.8

RUN pip install pipenv

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy

COPY . .

RUN aerich init -t tortoise_config.tortoise_config \
    && aerich init-db\
    && aerich migrate \
    && aerich upgrade 

RUN python -m bot