FROM nginxinc/nginx-unprivileged:1.25.4

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

# copy static files
WORKDIR /home/nginx/app
#COPY ./static_files .

# change ownership and permissions (needs root privileges)
USER root
RUN chown -R nginx:nginx . && chmod -R 755 .

# switch back to nginx user
USER nginx