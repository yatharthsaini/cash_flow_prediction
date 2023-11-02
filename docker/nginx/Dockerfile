FROM nginx:latest

RUN apt update
RUN apt upgrade -y

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d
