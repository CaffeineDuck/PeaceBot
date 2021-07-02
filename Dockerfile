FROM python:3.9.5-slim-buster

WORKDIR /bot

COPY . .

RUN pip install pipenv \ 
    && pipenv install --system --deploy --dev

CMD aerich init -t tortoise_config.tortoise_config\
    && aerich init-db\
    && aerich migrate\
    && aerich upgrade\
    && python -m bot
