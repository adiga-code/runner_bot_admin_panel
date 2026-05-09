# ── Stage 1: build ──────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_BASE_PATH=/runneradmintest/
ENV VITE_BASE_PATH=$VITE_BASE_PATH

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2: serve ──────────────────────────────────────────────
FROM nginx:alpine

ARG VITE_BASE_PATH=/runneradmintest/

# Copy built files into the subpath matching the base URL
COPY --from=builder /app/dist /usr/share/nginx/html${VITE_BASE_PATH}
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
