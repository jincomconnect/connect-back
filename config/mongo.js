const mongoose = require('mongoose');
const { MONGO_URI } = require('./env');

async function connectMongo() {
    await mongoose.connect(MONGO_URI);
    console.log('MongoDB connected');
}

module.exports = {
    connectMongo
};