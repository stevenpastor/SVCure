FROM python:3.6.8-alpine

LABEL image for annotating svs

WORKDIR /SVCure

COPY . .

RUN ["pip", "install", "-r", "requirements.txt"]
#RUN sed -i s/127\.0\.0\.1/0\.0\.0\.0/g SVCure/templates/annotation/example.html
#RUN sed -i s/127\.0\.0\.1/0\.0\.0\.0/g SVCure/templates/annotation/update.html

ENV FLASK_APP svcure
ENV FLASK_ENV development
RUN export FLASK_APP=svcure && export FLASK_ENV=development

