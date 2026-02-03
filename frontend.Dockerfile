# Etapa 1: Construcción (Build)
FROM node:18-alpine as build

WORKDIR /app

# Instalamos dependencias
COPY package*.json ./
RUN npm ci

# Copiamos todo el código fuente
COPY . .

# Construimos la aplicación para producción (genera carpeta 'dist')
RUN npm run build

# Etapa 2: Servir con Nginx
FROM nginx:alpine

# Copiamos la configuración personalizada de Nginx (para SPA)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiamos los archivos construidos de la etapa anterior a la carpeta de Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Exponemos el puerto 80 (standard web)
EXPOSE 80

# Nginx corre en primer plano por defecto
CMD ["nginx", "-g", "daemon off;"]
