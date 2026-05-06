// server.js
const app = require('./app');
const { PORT } = require('./config/env');
const { connectMongo } = require('./config/mongo');

async function startServer() {
    try {
        await connectMongo();
        const server = app.listen(PORT, () => {
            console.log(`Server running on port ${PORT}`);
        });

        server.on('error', (error) => {
            if (error.code === 'EADDRINUSE') {
                console.error(`Port ${PORT} is already in use. Stop the existing process or set a different PORT.`);
            } else {
                console.error('Server failed to start:', error);
            }

            process.exit(1);
        });
    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}

startServer();