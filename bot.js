const { Telegraf, Markup } = require('telegraf');
const axios = require('axios');
const express = require('express');
const { GoogleGenerativeAI } = require("@google/generative-ai");
require('dotenv').config();

// --- RENDER 7/24 AKTİF TUTMA (SUNUCU) ---
const app = express();
app.get('/', (req, res) => res.send('Irvus Bot 7/24 Aktif!'));
app.listen(process.env.PORT || 3000);

const bot = new Telegraf(process.env.BOT_TOKEN);
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

// Her grup için ayrı ayar tutan geçici hafıza
const db = {};

// --- KOMUTLAR ---

// 1. SETUP (AĞ SEÇİMİ)
bot.command('setup', (ctx) => {
    const chatId = ctx.chat.id;
    if (!db[chatId]) db[chatId] = { chain: null, ca: null, media: null, symbol: 'TOKEN' };

    return ctx.reply('🚀 Kurulum yapılacak ağı seçin:', 
        Markup.inlineKeyboard([
            [Markup.button.callback('Ethereum (ETH)', 'set_chain_eth'), Markup.button.callback('Solana (SOL)', 'set_chain_sol')],
            [Markup.button.callback('BSC (BNB)', 'set_chain_bsc'), Markup.button.callback('Base Chain', 'set_chain_base')]
        ])
    );
});

// 2. SETTINGS (GÖRSEL 2'DEKİ YAPI)
bot.command('settings', (ctx) => {
    const chatId = ctx.chat.id;
    const s = db[chatId] || {};
    
    const text = `⚙️ *Settings for this group*\n\n` +
                 `🌐 *Chain:* ${s.chain ? s.chain.toUpperCase() : 'Not set'}\n` +
                 `📑 *CA:* ${s.ca || 'Not set'}\n` +
                 `🎥 *Media:* ${s.media ? '✅ Uploaded' : '❌ Not set'}\n\n` +
                 `Select an option to configure:`;

    return ctx.replyWithMarkdown(text, 
        Markup.inlineKeyboard([
            [Markup.button.callback('📱 Telegram Link', 'noop'), Markup.button.callback('🌐 Website Link', 'noop')],
            [Markup.button.callback('📸 Add Media', 'add_media'), Markup.button.callback('➕ Add Token', 'add_token')],
            [Markup.button.callback('🗑️ Remove Token', 'reset')]
        ])
    );
});

// 3. AI SOR (/sor)
bot.command('sor', async (ctx) => {
    const query = ctx.message.text.split(' ').slice(1).join(' ');
    if (!query) return ctx.reply("Lütfen bir soru yazın. Örn: /sor Irvus nedir?");
    
    try {
        await ctx.sendChatAction('typing');
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        const result = await model.generateContent(query);
        ctx.reply(result.response.text(), { reply_to_message_id: ctx.message.message_id });
    } catch (e) { ctx.reply("Yapay zeka şu an meşgul."); }
});

// 4. AI ÇİZ (/ciz)
bot.command('ciz', async (ctx) => {
    const prompt = ctx.message.text.split(' ').slice(1).join(' ');
    if (!prompt) return ctx.reply("Ne çizmemi istersiniz?");
    
    try {
        await ctx.sendChatAction('upload_photo');
        const imageUrl = `https://pollinations.ai/p/${encodeURIComponent(prompt)}?width=1024&height=1024&model=flux`;
        await ctx.replyWithPhoto(imageUrl, { caption: `🎨 *Çizilen:* ${prompt}`, parse_mode: 'Markdown' });
    } catch (e) { ctx.reply("Görsel oluşturulamadı."); }
});

// --- BUTON VE MESAJ İŞLEME ---

bot.action(/set_chain_(.+)/, (ctx) => {
    const chain = ctx.match[1];
    db[ctx.chat.id] = { ...db[ctx.chat.id], chain: chain };
    ctx.answerCbQuery();
    ctx.reply(`✅ Ağ ${chain.toUpperCase()} olarak seçildi. Şimdi /settings'den CA ekleyin.`);
});

bot.action('add_token', (ctx) => ctx.reply("Lütfen Token Contract Address (CA) mesaj olarak gönderin."));
bot.action('add_media', (ctx) => ctx.reply("Lütfen Buy Alert videosunu veya GIF'ini gruba gönderin."));

// Video/GIF Yakalama
bot.on(['video', 'animation'], (ctx) => {
    const fileId = ctx.message.video ? ctx.message.video.file_id : ctx.message.animation.file_id;
    if (!db[ctx.chat.id]) db[ctx.chat.id] = {};
    db[ctx.chat.id].media = fileId;
    ctx.reply("✅ Medya kaydedildi! Artık Buy Alert'larda kullanılacak.");
});

// CA ve Rakamları Yakalama
bot.on('text', (ctx) => {
    const text = ctx.message.text;
    if (text.length > 30 && !text.includes('/')) {
        if (!db[ctx.chat.id]) db[ctx.chat.id] = {};
        db[ctx.chat.id].ca = text;
        ctx.reply(`✅ Token CA kaydedildi: ${text}`);
    }
});

// 5. BUY ALERT TESTİ (GÖRSEL 3 TASARIMI)
bot.command('testbuy', async (ctx) => {
    const s = db[ctx.chat.id] || {};
    const buyMessage = `
*iziri ($iziri) Buy!*
🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢

💰 *Spent:* $96.65
🌕 *Got:* 52.35M iziri
📊 *MCAP:* $1.85K
🧬 *Chain:* ${s.chain ? s.chain.toUpperCase() : 'Solana'}

🔗 [Chart](https://dexscreener.com)
    `;

    if (s.media) {
        await ctx.replyWithAnimation(s.media, { caption: buyMessage, parse_mode: 'Markdown' });
    } else {
        await ctx.replyWithMarkdown(buyMessage);
    }
});

bot.launch();
console.log("Irvus Bot Başlatıldı!");
