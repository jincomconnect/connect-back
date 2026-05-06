const jwt = require('jsonwebtoken');
const { JWT_SECRET } = require('../config/env');

function authenticateToken(req, res, next) {
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ message: 'Access denied' });
    }

    try {
        req.user = jwt.verify(token, JWT_SECRET);
        return next();
    } catch (_error) {
        return res.status(403).json({ message: 'Invalid token' });
    }
}

module.exports = {
    authenticateToken
};