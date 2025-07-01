FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev --legacy-peer-deps --no-audit --progress=false
COPY . .
RUN npm run build
CMD ["npm","start"]
