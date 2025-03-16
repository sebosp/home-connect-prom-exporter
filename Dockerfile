FROM python:3.13.2-alpine3.21
ADD requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt
WORKDIR /code
ADD app.py /code
CMD ["flask", "run", "--debug", "-h", "0.0.0.0", "-p", "8080"]
