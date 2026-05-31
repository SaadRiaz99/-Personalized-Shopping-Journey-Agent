FROM node:22-alpine

WORKDIR /app

COPY discoveryAgent.js .

CMD ["node", "discoveryAgent.js"]
