require('dotenv').config();

const PORT = Number(process.env.PORT) || 8080;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/auth-demo';
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const AUTOGEN_URL = process.env.AUTOGEN_URL || 'http://localhost:9000';
const ORCHESTRATOR_BEARER_TOKEN = process.env.ORCHESTRATOR_BEARER_TOKEN || 'change-me';
const ORCHESTRATOR_TIMEOUT_MS = Number(process.env.ORCHESTRATOR_TIMEOUT_MS) || 60000;
const CLIENT_ORIGINS = (process.env.CLIENT_ORIGIN || 'http://localhost:5173,http://127.0.0.1:5173')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean);

module.exports = {
    PORT,
    MONGO_URI,
    JWT_SECRET,
    AUTOGEN_URL,
    ORCHESTRATOR_BEARER_TOKEN,
    ORCHESTRATOR_TIMEOUT_MS,
    CLIENT_ORIGINS
};