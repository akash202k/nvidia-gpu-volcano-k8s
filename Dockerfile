FROM tensorflow/tensorflow:2.14.0-gpu
RUN pip install boto3
RUN apt-get remove -y curl wget git && \
    apt-get clean && \
    rm -rf /root/.cache /usr/local/cuda/doc/*

WORKDIR /app
COPY model/train.py .

CMD ["python", "train.py"]
