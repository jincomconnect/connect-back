const express = require('express');
const { authenticateToken } = require('../middleware/authenticateToken');
const {
    AUTOGEN_URL,
    ORCHESTRATOR_BEARER_TOKEN,
    ORCHESTRATOR_TIMEOUT_MS
} = require('../config/env');

const router = express.Router();

router.post('/agents/run', authenticateToken, async (req, res) => {
    if (typeof fetch !== 'function') {
        return res.status(500).json({
            message: 'Global fetch is unavailable. Use Node.js 18+ or add a fetch polyfill.'
        });
    }

    let timeout;

    try {
        const prompt = typeof req.body.prompt === 'string' ? req.body.prompt.trim() : '';
        const taskId = typeof req.body.taskId === 'string' ? req.body.taskId.trim() : '';
        const productContext = typeof req.body.productContext === 'string' ? req.body.productContext.trim() : '';

        if (!prompt || !taskId) {
            return res.status(400).json({ message: 'taskId and prompt are required' });
        }

        const controller = new AbortController();
        timeout = setTimeout(() => controller.abort(), ORCHESTRATOR_TIMEOUT_MS);

        const response = await fetch(`${AUTOGEN_URL}/orchestrate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${ORCHESTRATOR_BEARER_TOKEN}`
            },
            body: JSON.stringify({
                task_id: taskId,
                prompt,
                product_context: productContext
            }),
            signal: controller.signal
        });

        const data = await response.json();
        if (!response.ok) {
            return res.status(response.status).json({
                message: 'Orchestrator request failed',
                orchestrator: data
            });
        }

        return res.json(data);
    } catch (error) {
        if (error.name === 'AbortError') {
            return res.status(504).json({ message: 'Orchestrator timeout' });
        }

        return res.status(500).json({ message: 'Error calling orchestrator', error: error.message });
    } finally {
        if (timeout) {
            clearTimeout(timeout);
        }
    }
});

module.exports = router;
