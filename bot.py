import telebot
from telebot import types
import sqlite3

TOKEN = "8849350053:AAEA8K0W57Tlw-F4FYVuK6tcwQUPM8JknGc"
ADMIN_ID = 9273630562
REKENING = "DANA 085927969387"

bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("store.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, nama TEXT, saldo INTEGER DEFAULT 0, total_order INTEGER DEFAULT 0)")
cur.execute("CREATE TABLE IF NOT EXISTS produk (id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, nama TEXT, harga INTEGER, deskripsi TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS stok (id INTEGER PRIMARY KEY AUTOINCREMENT, produk_id INTEGER, kode TEXT, terjual INTEGER DEFAULT 0)")
conn.commit()

def init_produk():
    cur.execute("SELECT COUNT(*) FROM produk")
    if cur.fetchone()[0] == 0:
        data = [
            ("NIB", "NIB PT", 25000, "Jasa pembuatan NIB PT, resmi dari OSS. Proses cepat, file PDF dikirim ke kamu."),
        ]
        cur.executemany("INSERT INTO produk (kategori,nama,harga,deskripsi) VALUES (?,?,?,?)", data)
        conn.commit()
init_produk()

def get_user(uid, nama):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    u = cur.fetchone()
    if not u:
        cur.execute("INSERT INTO users VALUES (?,?,0,0)", (uid, nama))
        conn.commit()
        return (uid, nama, 0, 0)
    return u

def menu_utama():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🏪 Katalog", "💲 Deposit")
    m.add("🧾 Pesanan Saya", "🔍 Cek Kuota")
    m.add("👤 Akun Saya", "🎁 Referral")
    m.add("👑 Leaderboard", "💬 Bantuan")
    return m

@bot.message_handler(commands=['start'])
def start(msg):
    u = get_user(msg.from_user.id, msg.from_user.first_name)
    teks = f"👋 Selamat datang di Stecus Store!\n\n⊢ Nama : {u[1]}\n⊢ ID : {u[0]}\n⊢ Saldo : Rp{u[2]:,}\n⊢ Total Order : {u[3]}\n\n📌 Jual NIB PT Resmi - Rp 25.000\nPilih menu Katalog di bawah untuk order."
    bot.send_message(msg.chat.id, teks, reply_markup=menu_utama())

@bot.message_handler(func=lambda m: m.text == "🏪 Katalog")
def katalog(msg):
    teks = "🏪 Katalog Stecus Store\n\n📄 NIB - Jasa pembuatan NIB resmi dari OSS.\n\nPilih kategori:"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📄 NIB", callback_data="kat_NIB"))
    bot.send_message(msg.chat.id, teks, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("kat_"))
def list_produk(c):
    kat = c.data.replace("kat_", "")
    cur.execute("SELECT * FROM produk WHERE kategori=?", (kat,))
    rows = cur.fetchall()
    teks = f"📦 Kategori: {kat}\n\n"
    markup = types.InlineKeyboardMarkup()
    for r in rows:
        teks += f"{r[2]} - Rp{r[3]:,}\n{r[4]}\n\n"
        markup.add(types.InlineKeyboardButton(f"Beli {r[2]} - Rp{r[3]:,}", callback_data=f"beli_{r[0]}"))
    bot.send_message(c.message.chat.id, teks, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("beli_"))
def beli(c):
    pid = int(c.data.replace("beli_", ""))
    cur.execute("SELECT * FROM produk WHERE id=?", (pid,))
    p = cur.fetchone()
    uid = c.from_user.id
    cur.execute("SELECT saldo FROM users WHERE id=?", (uid,))
    saldo = cur.fetchone()[0]
    if saldo < p[3]:
        bot.send_message(c.message.chat.id, f"❌ Saldo kurang! Harga Rp{p[3]:,}, saldo kamu Rp{saldo:,}\nSilakan Deposit dulu.")
        return
    cur.execute("UPDATE users SET saldo=saldo-?, total_order=total_order+1 WHERE id=?", (p[3], uid))
    conn.commit()
    bot.send_message(c.message.chat.id, f"✅ Order Berhasil!\n\nProduk: {p[2]}\nHarga: Rp{p[3]:,}\n\nAdmin akan hubungi kamu untuk data pembuatan NIB (KTP, Nama Usaha, dll). Mohon tunggu ya!")
    bot.send_message(ADMIN_ID, f"ORDER BARU NIB\nDari: {c.from_user.first_name} ({uid})\nProduk: {p[2]} - Rp{p[3]:,}\n\nChat dia untuk minta data KTP / Usaha.")

@bot.message_handler(func=lambda m: m.text == "💲 Deposit")
def deposit(msg):
    bot.send_message(msg.chat.id, f"💲 Deposit Saldo\n\nTransfer ke:\n{REKENING}\n\nMinimal Rp 25.000\nSetelah transfer, kirim bukti ke sini, admin akan isi saldo kamu.")

@bot.message_handler(func=lambda m: m.text == "👤 Akun Saya")
def akun(msg):
    u = get_user(msg.from_user.id, msg.from_user.first_name)
    bot.send_message(msg.chat.id, f"👤 Akun Saya\n\nNama: {u[1]}\nID: {u[0]}\nSaldo: Rp{u[2]:,}\nTotal Order: {u[3]}")

@bot.message_handler(commands=['isi'])
def isi(msg):
    if msg.from_user.id != ADMIN_ID: return
    try:
        _, uid, jml = msg.text.split()
        cur.execute("UPDATE users SET saldo=saldo+? WHERE id=?", (int(jml), int(uid)))
        conn.commit()
        bot.reply_to(msg, f"Saldo {uid} ditambah Rp{int(jml):,}")
        bot.send_message(int(uid), f"✅ Deposit Rp{int(jml):,} berhasil masuk!")
    except:
        bot.reply_to(msg, "Cara: /isi 123456789 25000")

print("Bot jalan...")
bot.polling()
