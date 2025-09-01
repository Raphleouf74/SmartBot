
const express = require("express");
const app = express();
const port = 3001;

app.use(express.json());

// Exemple de config du bot
let botConfig = {
  prefix: "!",
  welcomeMessage: "Bienvenue sur SmartHub 🎉"
};

// GET status
app.get("/status", (req, res) => {
  res.json({
    online: true,
    servers: global.client.guilds.cache.size,
    users: global.client.users.cache.size
  });
});

// GET config
app.get("/config", (req, res) => {
  res.json(botConfig);
});

// POST config (mise à jour depuis le dashboard)
app.post("/config", (req, res) => {
  botConfig = { ...botConfig, ...req.body };
  res.json({ success: true, config: botConfig });
});

// Lancer serveur
app.listen(port, () => console.log(`Bot API running at http://localhost:${port}`));
