# Stage 1 — Build the Vue app
FROM node:22-slim AS builder

WORKDIR /app

# Copy package files first (caching trick)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the Vue app for production
RUN npm run build

# Stage 2 — Serve with Nginx
FROM nginx:alpine

# Copy the built files to Nginx's serve folder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80