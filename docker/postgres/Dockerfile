FROM postgres:15
RUN apt-get update && apt-get install -y locales \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*
ENV LANG en_US.UTF-8

# Ensure MD5 authentication
COPY pg_hba.conf /etc/postgresql/pg_hba.conf
COPY init-pg_hba.sh /docker-entrypoint-initdb.d/10_init_pg_hba.sh
COPY postgresql.conf /etc/postgresql/postgresql.conf
RUN chmod 0644 /etc/postgresql/pg_hba.conf && \
    chmod +x /docker-entrypoint-initdb.d/10_init_pg_hba.sh

# Use provided entrypoint
EXPOSE 5432
