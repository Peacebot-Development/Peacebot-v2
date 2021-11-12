FROM python:3.9-slim-buster


# Creating workdir and copying the config and lock files for poetry
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Installing the system dependencies
RUN apt-get update && apt-get install git -y \
    && pip install poetry 

# Installing the python dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Running the bot
COPY . /code
RUN chmod +x entrypoint.sh
ENTRYPOINT [ "sh", "entrypoint.sh" ]
