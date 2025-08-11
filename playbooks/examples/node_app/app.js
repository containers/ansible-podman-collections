const express = require('express');
const app = express();

app.get('/predict', (req, res) => {
  // Dummy prediction endpoint
  res.json({ prediction: Math.random() });
});

app.listen(3000, () => console.log('AI prediction API listening on :3000'));


