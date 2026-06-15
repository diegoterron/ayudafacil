FROM node:20-alpine

WORKDIR /app

# Copiar package.json y package-lock.json para instalar dependencias
COPY package.json package-lock.json ./

# Instalar dependencias
RUN npm install

# Copiar el código fuente
COPY . .

# Exponer el puerto de desarrollo de Vite
EXPOSE 5173

# Arrancar el servidor de desarrollo de Vite expuesto en red (para poder acceder desde el host)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
