const { Telegraf, Markup } = require('telegraf');
const axios = require('axios');
const express = require('express');
const { GoogleGenerativeAI } = require("@google/generative-ai");
require('dotenv').config();

// Render'da uyumaması için basit web sunucusu
const app = express();
app.get('/', (req, res) => res.send('Irvus Bot Aktif!'));
app.listen(process.env.PORT || 3000);

const bot = new Telegraf(process.env.BOT_TOKEN);
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

// Geçici Veritabanı (Render'da kalıcı olması için MongoDB bağlamanı öneririm)
// Bu nesne her grubun ayarlarını (CA, ağ, video) ayrı tutar
const db = {};

// --- KOMUTLAR ---

// 1. SETUP KOMUTU (Ağ Seçimi)
bot.command('setup', (ctx) => {
    const chatId = ctx.chat.id;
    if (!db[chatId]) db[chatId] = { chain: null, ca: null, media: null };

    return ctx.reply('🚀 Kurulum yapılacak ağı seçin:', 
        Markup.inlineKeyboard([
            [Markup.button.callback('Ethereum', 'set_chain_eth'), Markup.button.callback('Solana', 'set_chain_sol')],
            [Markup.button.callback('BSC', 'set_chain_bsc'), Markup.button.callback('Base', 'set_chain_base')]
        ])
    );
});

// 2. AYARLAR (2. Görseldeki Yapı)
bot.command('settings', (ctx) => {
    const chatId = ctx.chat.id;
    const settings = db[chatId] || { chain: 'Not set', ca: 'Not set', media: '❌' };
    
    const text = `⚙️ Settings for this group\n\n` +
                 `🌐 Chain: ${settings.chain || 'Not set'}\n` +
                 `📑 CA: ${settings.ca || 'Not set'}\n` +
                 `🎥 Media: ${settings.media ? '✅ Uploaded' : '❌ Not set'}\n` +
                 `Select an option to configure:`;

    return ctx.reply(text, 
        Markup.inlineKeyboard([
            [Markup.button.callback('📱 Telegram Link', 'noop'), Markup.button.callback('🌐 Website Link', 'noop')],
            [Markup.button.callback('📸 Add Media', 'add_media'), Markup.button.callback('➕ Add Token', 'add_token')],
            [Markup.button.callback('🗑️ Remove Token', 'remove_token')]
        ])
    );
});

// 3. AI SOR KOMUTU
bot.command('sor', async (ctx) => {
    const query = ctx.message.text.split(' ').slice(1).join(' ');
    if (!query) return ctx.reply("Lütfen bir soru sorun. Örnek: /sor Irvus Token nedir?");

    try {
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        const result = await model.generateContent(query);
        ctx.reply(result.response.text(), { reply_to_message_id: ctx.message.message_id });
    } catch (e) { ctx.reply("AI şu an meşgul."); }
});

// 4. AI ÇİZ KOMUTU
bot.command('ciz', async (ctx) => {
    const prompt = ctx.message.text.split(' ').slice(1).join(' ');
    if (!prompt) return ctx.reply("Ne çizmemi istersiniz?");
    
    const imageUrl = `https://pollinations.ai/p/${encodeURIComponent(prompt)}?width=1024&height=1024&model=flux`;
    await ctx.replyWithPhoto(imageUrl, { caption: `🎨 Çizilen: ${prompt}` });
});

// --- CALLBACK HANDLERS (Buton Tıklamaları) ---

bot.action(/set_chain_(.+)/, (ctx) => {
    const chain = ctx.match[1];
    db[ctx.chat.id] = { ...db[ctx.chat.id], chain: chain };
    ctx.answerCbQuery();
    ctx.reply(`✅ Ağ ${chain.toUpperCase()} olarak seçildi. Şimdi /settings kısmından CA ekleyin.`);
});

bot.action('add_media', (ctx) => {
    ctx.reply("Lütfen buy alert mesajında görünecek bir Video veya GIF gönderin.");
    // Burada bir sonraki mesajı dinleme mantığı kurulabilir
});

// --- BUY ALERT SİMÜLASYONU (3. Görseldeki Tasarım) ---
// Not: Gerçek alımları dinlemek için DexScreener WebSocket entegrasyonu gerekir.
bot.command('testbuy', (ctx) => {
    const chatId = ctx.chat.id;
    const settings = db[chatId];
    
    const buyMessage = `
${settings?.symbol || 'Irvus'} ($IRVUS) Buy!
🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢

💰 Spent: $96.65
🌕 Got: 52.35M IRVUS
📊 MCAP: $1.85K
🧬 Chain: ${settings?.chain || 'Solana'}

🔗 [Chart](https://dexscreener.com)
    `;

    // Eğer video yüklenmişse video ile, yoksa metin atar
    if (settings?.mediaId) {
        ctx.replyWithVideo(settings.mediaId, { caption: buyMessage, parse_mode: 'Markdown' });
    } else {
        ctx.reply(buyMessage, { parse_mode: 'Markdown' });
    }
});

bot.launch();
console.log("Bot çalışıyor...");
