FROM node:18-alpine
WORKDIR /app
COPY app/admin/package*.json ./
RUN npm ci
COPY app/admin .
RUN npm run build
