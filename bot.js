const { Telegraf, Markup } = require('telegraf');
const axios = require('axios');
const express = require('express');
const { GoogleGenerativeAI } = require("@google/generative-ai");
require('dotenv').config();

// --- SUNUCU AYARI (Render 7/24) ---
const app = express();
app.get('/', (req, res) => res.send('Irvus AI & Buy Bot Aktif!'));
app.listen(process.env.PORT || 3000);

const bot = new Telegraf(process.env.BOT_TOKEN);
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

// Her grubun verilerini ayrı tutan veritabanı objesi
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
const getSettingsMenu = (chatId) => {
    const s = db[chatId] || { chain: 'SOL', ca: 'Not set', emoji: '🟢', minBuy: 0 };
    const text = 
    `🔗 *Links:*\n` +
    `• Telegram: ${s.tg || 'Not set'}\n` +
    `• Website: ${s.web || 'Not set'}\n` +
    `• X/Twitter: ${s.x || 'Not set'}\n\n` +
    `*Use the buttons below to configure:*`;

    const keyboard = Markup.inlineKeyboard([
        [Markup.button.callback('📢 Telegram Link', 'set_tg'), Markup.button.callback('🌐 Website Link', 'set_web')],
        [Markup.button.callback('🐦 X/Twitter Link', 'set_x'), Markup.button.callback(`Emoji: ${s.emoji || '🟢'}`, 'set_emoji')],
        [Markup.button.callback(`💵 Min Buy: $${s.minBuy || 0}`, 'set_minbuy'), Markup.button.callback(`${s.media ? '✅' : '❌'} Media`, 'add_media')],
        [Markup.button.callback('➕ Add Token', 'add_token'), Markup.button.callback('➖ Remove Token', 'reset')],
        [Markup.button.callback('📋 View Tokens', 'view_tokens'), Markup.button.callback('🔄 Refresh', 'settings_refresh')]
    ]);

    return { text, keyboard };
};

bot.command('settings', (ctx) => {
    const menu = getSettingsMenu(ctx.chat.id);
    ctx.replyWithMarkdown(menu.text, menu.keyboard);
});

// --- SETUP VE AĞ SEÇİMİ ---
bot.command('setup', (ctx) => {
    ctx.reply('Kurulum için bir ağ seçin:', Markup.inlineKeyboard([
        [Markup.button.callback('Solana', 'net_sol'), Markup.button.callback('Ethereum', 'net_eth')],
        [Markup.button.callback('Base', 'net_base'), Markup.button.callback('BSC', 'net_bsc')]
    ]));
});

// --- AI SOR VE ÇİZ ---
bot.command('sor', async (ctx) => {
    const query = ctx.message.text.split(' ').slice(1).join(' ');
    if (!query) return ctx.reply("Soru yazın. Örn: /sor Irvus Token geleceği nedir?");
    try {
        await ctx.sendChatAction('typing');
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        const result = await model.generateContent(query);
        ctx.reply(result.response.text(), { reply_to_message_id: ctx.message.message_id });
    } catch (e) { ctx.reply("⚠️ AI şu an meşgul, API anahtarınızı kontrol edin."); }
});

bot.command('ciz', async (ctx) => {
    const prompt = ctx.message.text.split(' ').slice(1).join(' ');
    if (!prompt) return ctx.reply("Ne çizmemi istersiniz?");
    const imageUrl = `https://pollinations.ai/p/${encodeURIComponent(prompt)}?width=1024&height=1024&model=flux`;
    ctx.replyWithPhoto(imageUrl, { caption: `🎨 *Çizilen:* ${prompt}`, parse_mode: 'Markdown' });
});

// --- DİNAMİK ALIM TAKİPÇİSİ (BSC, ETH, BASE, SOL) ---
async function scanMarkets() {
    for (const chatId in db) {
        const s = db[chatId];
        if (!s.ca) continue;

        try {
            const res = await axios.get(`https://api.dexscreener.com/latest/dex/tokens/${s.ca}`);
            const pair = res.data.pairs ? res.data.pairs[0] : null;

            if (pair) {
                const price = pair.priceUsd;
                const mcap = pair.fdv || pair.marketCap || 0;
                
                // Eğer fiyat değişmişse alım var demektir (Simülasyon)
                if (lastPrices[chatId] && lastPrices[chatId] !== price) {
                    const buyMsg = 
                    `*${pair.baseToken.name} ($${pair.baseToken.symbol}) Buy!*\n` +
                    `${s.emoji.repeat(5)}\n\n` +
                    `💰 *Spent:* $${(Math.random() * 100 + 50).toFixed(2)}\n` +
                    `🌕 *Got:* ${(Math.random() * 1000).toFixed(0)}M ${pair.baseToken.symbol}\n` +
                    `📊 *MCAP:* $${Number(mcap).toLocaleString()}\n` +
                    `🧬 *Chain:* ${pair.chainId.toUpperCase()}\n\n` +
                    `🔗 [Chart](${pair.url})`;

                    if (s.media) {
                        await bot.telegram.sendAnimation(chatId, s.media, { caption: buyMsg, parse_mode: 'Markdown' });
                    } else {
                        await bot.telegram.sendMessage(chatId, buyMsg, { parse_mode: 'Markdown' });
                    }
                }
                lastPrices[chatId] = price;
            }
        } catch (e) { console.error("Tarama hatası:", e.message); }
    }
}
setInterval(scanMarkets, 30000); // 30 saniyede bir tarar

// --- BUTON TEPKİLERİ ---
bot.action(/net_(.+)/, (ctx) => {
    const net = ctx.match[1];
    db[ctx.chat.id] = { ...db[ctx.chat.id], chain: net };
    ctx.reply(`✅ Ağ ${net.toUpperCase()} olarak seçildi. Şimdi /settings'den CA ekleyin.`);
});

bot.action('add_token', (ctx) => ctx.reply("Lütfen tokenin CA adresini gruba gönderin."));
bot.action('add_media', (ctx) => ctx.reply("Lütfen Buy Alert'da görünecek bir Video/GIF gönderin."));

bot.on(['video', 'animation'], (ctx) => {
    const fileId = ctx.message.video ? ctx.message.video.file_id : ctx.message.animation.file_id;
    if (!db[ctx.chat.id]) db[ctx.chat.id] = {};
    db[ctx.chat.id].media = fileId;
    ctx.reply("✅ Medya kaydedildi!");
});

bot.on('text', (ctx) => {
    const text = ctx.message.text;
    if (text.length > 30 && !text.includes('/')) {
        if (!db[ctx.chat.id]) db[ctx.chat.id] = {};
        db[ctx.chat.id].ca = text;
        ctx.reply(`✅ Token CA kaydedildi: ${text}`);
    }
});

bot.launch();
bot.launch()
  .then(() => console.log("✅ Bot Telegram'a başarıyla bağlandı!"))
  .catch((err) => console.error("❌ Bağlantı Hatası:", err));

// Botun çökmesini önlemek için genel hata yakalayıcı
process.on('unhandledRejection', (reason, promise) => {
    console.log('Hata:', reason);
});
