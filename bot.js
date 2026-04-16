const { Telegraf, Markup } = require('telegraf');
const axios = require('axios');
const express = require('express');
const { GoogleGenerativeAI } = require("@google/generative-ai");
require('dotenv').config();

// --- 7/24 AKTİF TUTMA SUNUCUSU ---
const app = express();
app.get('/', (req, res) => res.send('Irvus AI Bot Live!'));
app.listen(process.env.PORT || 3000);

if (!process.env.BOT_TOKEN) {
    console.error("HATA: BOT_TOKEN Environment Variable olarak eklenmemiş!");
    process.exit(1);
}

const bot = new Telegraf(process.env.BOT_TOKEN);
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "");

const db = {};
const lastPrices = {};

// --- 3. GÖRSELDEKİ START MENÜSÜ ---
bot.command('start', (ctx) => {
    const startText = 
    `🤖 *Buy Bot — Commands*\n` +
    `⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n` +
    `🔧 *Admin Commands:*\n` +
    `/setup — Configure the bot for your group\n` +
    `/settings — Open the settings dashboard\n` +
    `/testbuy — Fire a test buy alert right now\n` +
    `/diag — Show diagnostics & monitor state\n\n` +
    `📊 *Token Commands:*\n` +
    `/price — Current price, MCAP, 5m buys/sells\n\n` +
    `🤖 *AI Commands:*\n` +
    `/sor question — Ask the AI assistant\n` +
    `/ciz prompt — Generate an AI image\n\n` +
    `💬 *AI Chat:*\n` +
    `Mention @${ctx.botInfo.username} with any question!`;

    ctx.replyWithMarkdown(startText);
});

// --- 4. GÖRSELDEKİ SETTINGS MENÜSÜ ---
bot.command('settings', (ctx) => {
    const s = db[ctx.chat.id] || { chain: 'SOL', ca: 'Not set', emoji: '🟢', minBuy: 0 };
    const text = 
    `🔗 *Links:*\n` +
    `• Telegram: ${s.tg || 'Not set'}\n` +
    `• Website: ${s.web || 'Not set'}\n` +
    `• X/Twitter: ${s.x || 'Not set'}\n\n` +
    `*Use the buttons below to configure:*`;

    const keyboard = Markup.inlineKeyboard([
        [Markup.button.callback('📢 Telegram Link', 'set_tg'), Markup.button.callback('🌐 Website Link', 'set_web')],
        [Markup.button.callback('🐦 X/Twitter Link', 'set_x'), Markup.button.callback(`Emoji: ${s.emoji || '🟢'}`, 'noop')],
        [Markup.button.callback(`💵 Min Buy: $${s.minBuy || 0}`, 'noop'), Markup.button.callback(`${s.media ? '✅' : '❌'} Media`, 'add_media')],
        [Markup.button.callback('➕ Add Token', 'add_token'), Markup.button.callback('➖ Remove Token', 'reset')],
        [Markup.button.callback('📋 View Tokens', 'noop'), Markup.button.callback('🔄 Refresh', 'settings_refresh')]
    ]);

    ctx.replyWithMarkdown(text, keyboard);
});

// --- AI KOMUTLARI ---
bot.command('sor', async (ctx) => {
    const query = ctx.message.text.split(' ').slice(1).join(' ');
    if (!query) return ctx.reply("Lütfen bir soru yazın.");
    try {
        await ctx.sendChatAction('typing');
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        const result = await model.generateContent(query);
        ctx.reply(result.response.text());
    } catch (e) { ctx.reply("⚠️ AI şu an meşgul, API anahtarını kontrol edin."); }
});

bot.command('ciz', async (ctx) => {
    const prompt = ctx.message.text.split(' ').slice(1).join(' ');
    if (!prompt) return ctx.reply("Ne çizmemi istersiniz?");
    const imageUrl = `https://pollinations.ai/p/${encodeURIComponent(prompt)}?width=1024&height=1024&model=flux`;
    ctx.replyWithPhoto(imageUrl, { caption: `🎨 *Çizilen:* ${prompt}`, parse_mode: 'Markdown' });
});

// --- ALIM TAKİP SİSTEMİ (DexScreener API) ---
async function scanMarkets() {
    for (const chatId in db) {
        const s = db[chatId];
        if (!s.ca) continue;

        try {
            const res = await axios.get(`https://api.dexscreener.com/latest/dex/tokens/${s.ca}`);
            const pair = res.data.pairs ? res.data.pairs[0] : null;

            if (pair) {
                
