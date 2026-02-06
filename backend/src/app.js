const express = require('express');
const cors = require('cors');
const path = require('path');
const optimizationRoutes = require('./routes/optimization');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use('/api', optimizationRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`Velora Backend running on port ${PORT}`);
});

module.exports = app;
