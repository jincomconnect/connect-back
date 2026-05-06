const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const { JWT_SECRET } = require('../config/env');
const { authenticateToken } = require('../middleware/authenticateToken');

const router = express.Router();

function normalizeEmail(email = '') {
    return email.trim().toLowerCase();
}

function createAuthResponse(user, message) {
    const token = jwt.sign(
        { userId: user._id.toString(), email: user.email },
        JWT_SECRET,
        { expiresIn: '1h' }
    );

    return {
        message,
        token,
        user: {
            id: user._id.toString(),
            email: user.email
        }
    };
}

router.post('/signup', async (req, res) => {
    try {
        const email = normalizeEmail(req.body.email);
        const { password } = req.body;

        if (!email || !password) {
            return res.status(400).json({ message: 'Email and password are required' });
        }

        if (password.length < 6) {
            return res.status(400).json({ message: 'Password must be at least 6 characters' });
        }

        const existingUser = await User.findOne({ email });
        if (existingUser) {
            return res.status(400).json({ message: 'User already exists' });
        }

        const hashedPassword = await bcrypt.hash(password, 10);
        const user = await User.create({
            email,
            password: hashedPassword
        });

        return res.status(201).json(createAuthResponse(user, 'User created successfully'));
    } catch (error) {
        return res.status(500).json({ message: 'Error creating user', error: error.message });
    }
});

router.post('/login', async (req, res) => {
    try {
        const email = normalizeEmail(req.body.email);
        const { password } = req.body;

        if (!email || !password) {
            return res.status(400).json({ message: 'Email and password are required' });
        }

        const user = await User.findOne({ email });
        if (!user) {
            return res.status(400).json({ message: 'Invalid credentials' });
        }

        const isValidPassword = await bcrypt.compare(password, user.password);
        if (!isValidPassword) {
            return res.status(400).json({ message: 'Invalid credentials' });
        }

        return res.json(createAuthResponse(user, 'Login successful'));
    } catch (error) {
        return res.status(500).json({ message: 'Error logging in', error: error.message });
    }
});

router.get('/me', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId).select('_id email');

        if (!user) {
            return res.status(404).json({ message: 'User not found' });
        }

        return res.json({
            user: {
                id: user._id.toString(),
                email: user.email
            }
        });
    } catch (error) {
        return res.status(500).json({ message: 'Error fetching user', error: error.message });
    }
});

router.get('/protected', authenticateToken, (req, res) => {
    return res.json({
        message: 'This is a protected route',
        userId: req.user.userId,
        email: req.user.email
    });
});

module.exports = router;