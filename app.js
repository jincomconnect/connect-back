const cors = require('cors');
const express = require('express');
const authRoutes = require('./routes/auth');
const agentRoutes = require('./routes/agents');
const { CLIENT_ORIGINS } = require('./config/env');

const app = express();

app.use(cors({
    origin(origin, callback) {
        if (!origin || CLIENT_ORIGINS.includes(origin)) {
            callback(null, true);
            return;
        }

        callback(new Error('Origin not allowed by CORS'));
    },
    credentials: true
}));
app.use(express.json());

app.get('/api/health', (_req, res) => {
    res.json({ status: 'ok' });
});

app.use('/api', authRoutes);
app.use('/api', agentRoutes);

module.exports = app;