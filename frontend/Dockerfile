FROM node:22-alpine

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend /app/frontend
COPY erato-design-system /app/erato-design-system

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
