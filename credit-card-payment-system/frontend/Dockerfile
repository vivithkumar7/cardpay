FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
RUN ROLLUP_VERSION=$(node -p "require('./node_modules/rollup/package.json').version") \
    && npm install --no-save "@rollup/rollup-linux-x64-musl@${ROLLUP_VERSION}"
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
