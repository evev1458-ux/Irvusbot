const { Telegraf, Markup } = require('telegraf');
const axios = require('axios');
const express = require('express');
const { GoogleGenerativeAI } = require("@google/generative-ai");
require('dotenv').config();

// Render 7/24 Aktif Tutma
const app = express();
app.get('/', (req, res) => res.send('Irvus AI Bot Live!'));
app.listen(process.env.PORT || 3000);

const bot = new Telegraf(process.env.BOT_TOKEN);
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "");

const db = {};
const lastPrices = {};

// --- START MENÜSÜ ---
bot.command('start', (ctx) => {
    const startText = 
    `🤖 *Buy Bot — Commands*\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n` +
    `🔧 *Admin Commands:*\n/setup — Configure group\n/settings — Settings dashboard\n/testbuy — Fire test alert\n/diag — Monitor state\n\n` +
    `📊 *Token Commands:*\n/price — Current price & MCAP\n\n` +
    `🤖 *AI Commands:*\n/sor question — Ask AI\n/ciz prompt — Generate image\n\n` +
    `💬 *AI Chat:*\nMention @${ctx.botInfo.username} any question!`;
    ctx.replyWithMarkdown(startText);
});

// --- SETTINGS MENÜSÜ ---
bot.command('settings', (ctx) => {
    const s = db[ctx.chat.id] || { chain: 'SOL', ca: 'Not set' };
    const text = `🔗 *Links:*\n• Telegram: ${s.tg || 'Not set'}\n• Website: ${s.web || 'Not set'}\n• X: ${s.x || 'Not set'}\n\n*Configure:*`;
    const keyboard = Markup.inlineKeyboard([
        [Markup.button.callback('📢 Telegram Link', 'set_tg'), Markup.button.callback('🌐 Website Link', 'set_web')],
        [Markup.button.callback('🐦 X/Twitter Link', 'set_x'), Markup.button.callback('Emoji: 🟢', 'noop')],
        [Markup.button.callback('➕ Add Token', 'add_token'), Markup.button.callback('✅ Media', 'add_media')],
        [Markup.button.callback('🔄 Refresh', 'settings_refresh')]
    ]);
    ctx.replyWithMarkdown(text, keyboard);
});

// --- AI SOR & CIZ ---
bot.command('sor', async (ctx) => {
    const query = ctx.message.text.split(' ').slice(1).join(' ');
    if (!query) return ctx.reply("Soru yazın.");
    try {
        await ctx.sendChatAction('typing');
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        const result = await model.generateContent(query);
        ctx.reply(result.response.text());
    } catch (e) { ctx.reply("⚠️ AI meşgul."); }
});

bot.command('ciz', async (ctx) => {
    const prompt = ctx.message.text.split(' ').slice(1).join(' ');
    if (!prompt) return ctx.reply("Ne çizeyim?");
    const imageUrl = `https://pollinations.ai/p/${encodeURIComponent(prompt)}?width=1024&height=1024&model=flux`;
    ctx.replyWithPhoto(imageUrl, { caption: `🎨 *Çizilen:* ${prompt}`, parse_mode: 'Markdown' });
});

// --- ALIM TAKİBİ ---
async function scan() {
    for (const id in db) {
        if (!db[id].ca) continue;
        try {
            const res = await axios.get(`https://api.dexscreener.com/latest/dex/tokens/${db[id].ca}`);
            const p = res.data.pairs ? res.data.pairs[0] : null;
            if (p && lastPrices[id] !== p.priceUsd) {
                const msg = `🟢 *${p.baseToken.symbol} Buy!*\n🟢🟢🟢🟢🟢🟢🟢🟢\n\n💰 *Price:* $${p.priceUsd}\n📊 *MCAP:* $${Number(p.fdv || p.marketCap).toLocaleString()}\n\n🔗 [Chart](${p.url})`;
                if (db[id].media) await bot.telegram.sendAnimation(id, db[id].media, { caption: msg, parse_mode: 'Markdown' });
                else await bot.telegram.sendMessage(id, msg, { parse_mode: 'Markdown' });
                lastPrices[id] = p.priceUsd;
            }
        } catch (e) {}
    }
}
setInterval(scan, 30000);

// --- SETUP & HANDLERS ---
bot.command('setup', (ctx) => {
    ctx.reply('Ağ seçin:', Markup.inlineKeyboard([
        [Markup.button.callback('Solana', 'n_sol'), Markup.button.callback('Base', 'n_base')],
        [Markup.button.callback('Ethereum', 'n_eth'), Markup.button.callback('BSC', 'n_bsc')]
    ]));
});

bot.action(/n_(.+)/, (ctx) => {
    db[ctx.chat.id] = { ...db[ctx.chat.id], chain: ctx.match[1] };
    ctx.reply(`✅ Ağ kaydedildi. CA gönderin.`);
});

bot.action('add_token', (ctx) => ctx.reply("CA gönderin."));
bot.action('add_media', (ctx) => ctx.reply("Video/GIF gönderin."));

bot.on(['video', 'animation'], (ctx) => {
    const fid = ctx.message.video ? ctx.message.video.file_id : ctx.message.animation.file_id;
    db[ctx.chat.id] = { ...db[ctx.chat.id], media: fid };
    ctx.reply("✅ Medya kaydedildi.");
});

bot.on('text', (ctx) => {
    const t = ctx.message.text;
    if (t.length > 30 && !t.includes('/')) {
        db[ctx.chat.id] = { ...db[ctx.chat.id], ca: t };
        ctx.reply(`✅ CA kaydedildi: ${t}`);
    }
});

// --- BAŞLATICI ---
bot.launch({ dropPendingUpdates: true })
    .then(() => console.log("✅ Bot Hazır!"))
    .catch((err) => console.error("Hata:", err));
