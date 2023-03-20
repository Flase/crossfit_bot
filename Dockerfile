FROM python:3.9
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./ /code
# CMD ["uvicorn", "--host", "0.0.0.0", "--port", "3222", "main:app"]
CMD ["python", "-m", "main"]
