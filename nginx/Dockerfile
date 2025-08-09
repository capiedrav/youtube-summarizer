FROM nginxinc/nginx-unprivileged:1.25.4

# copy config file
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

# folder for storing static and media files
WORKDIR /usr/share/nginx/html
