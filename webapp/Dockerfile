FROM node:20-alpine
WORKDIR /app
COPY webapp/package*.json ./
RUN npm ci
COPY webapp ./
EXPOSE 3000
CMD ["npm","run","dev"]
