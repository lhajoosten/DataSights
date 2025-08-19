# ...existing code...
FROM node:18-alpine AS build
WORKDIR /app

# Install deps
COPY package*.json ./
RUN npm ci --silent

# Copy source and build; allow API base URL injection at build time
COPY . .
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Serve with lightweight nginx
FROM nginx:stable-alpine
# Remove default html
RUN rm -rf /usr/share/nginx/html/*
# (optional) remove any packaged default conf so our conf replaces it cleanly
RUN rm -f /etc/nginx/conf.d/default.conf || true
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config that proxies /api to the backend service
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]