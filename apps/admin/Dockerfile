FROM node:18-alpine
WORKDIR /app
COPY apps/admin/package*.json ./
RUN npm ci
COPY apps/admin .
RUN npm run build
