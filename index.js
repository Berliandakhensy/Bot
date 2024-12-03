const { Client, GatewayIntentBits } = require('discord.js');
const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.once('ready', () => {
    console.log('Bot is online!');
});

client.login('MTMxMTg0NzMyNjg3MTk3ODAyNQ.GEhQij.OiNGIoGTJ1ZvcbkLTLs4pn_isP82h3-NAhhVic');
