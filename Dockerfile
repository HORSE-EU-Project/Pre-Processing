FROM python:3.9.12

WORKDIR /dff

COPY requirements.txt schema.sql user.py db.py app.py ./
COPY ./Web_app ./Web_app
COPY ./templates ./templates
COPY ./static ./static

RUN pip --no-cache-dir install -r requirements.txt

CMD ["python3", "app.py"]