FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

WORKDIR /app

# install dependencies
COPY ./requirements.txt .
RUN pip install --no-cache -r requirements.txt

# create non-root user   
RUN adduser --disabled-password --no-create-home app-user

# copy source code
COPY ./source ./source

# change ownership and permissions of the files
RUN chown -R app-user:users . && chmod 700 -R .

# move to source directory
WORKDIR /app/source

# switch to app-user
USER app-user

# start the app
CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000" ]
