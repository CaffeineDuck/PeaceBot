FROM python:3.8.6

LABEL name="peace_bot"

LABEL version="1.0"

LABEL description="PeaceBot Docker Image"

RUN pip install pipenv

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy

COPY . .

RUN aerich init -t tortoise_config.tortoise_config \
    && aerich init-db \
    && aerich migrate \
    && aerich upgrade 

RUN python -m bot