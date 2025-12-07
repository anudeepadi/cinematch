# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build argument for API URL (set at build time)
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build the app
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine

# Copy nginx config as template (nginx will substitute $PORT at runtime)
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Default port (Railway will override via $PORT)
ENV PORT=80

# Expose dynamic port
EXPOSE $PORT

CMD ["nginx", "-g", "daemon off;"]
