import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
import hashlib
import codecs
from random import randint
from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.const import Assets
crypto = AioCryptoPay(token='26525:AAl1U0uZjhGHNOfLASgPvO1iWpTFbAu6L9g', network=Networks.TEST_NET)
storage = MemoryStorage()
class Form(StatesGroup):
    waiting_for_amount = State()
class Pay(StatesGroup):
    waiting_for_count = State()
with codecs.open('config.bot.ini','r', encoding='utf-8') as config_file:
	for line in config_file:
		if '"' in line:
			zer = u"" + line.replace('"',"").replace('\r','').replace('^', '\n')
			zen = zer.split('=')
			globals()[zen[0]] = zen[1]
def md5(data):
	md5_hash = hashlib.md5()
	md5_hash.update(data.encode('utf-8'))
	return md5_hash.hexdigest()
# DB
db_users = {}
db_stock = {}
db_countries = {}
ranks = {}
# DB
with codecs.open('users.ini','r', encoding='utf-8') as users_file:
	i = 0
	for line in users_file:
		if '=' in line:
			zer = u"" + line.replace('"',"")
			zen = zer.split('=')
			zep = zen[1].split(',')
			db_users[int(zen[0])] = [float(zep[0]), zep[1], int(zep[2]), int( zep[3])]
			ranks[int(zen[0])] = int(zep[2])
		i += 1
	print(f'Loaded {i} users')
with codecs.open('countries.bot.ini','r', encoding='utf-8') as config_file:
	for line in config_file:
		if '"' in line:
			zer = u"" + line.replace('"',"").replace('\r','')
			zen = zer.split('=')
			langs = zen[1].split(",")
			languages = {"ru":  langs[0], "ua": langs[1], "en": langs[2]}
			db_countries[zen[0]] = languages
			db_stock[zen[0]] = 0
with codecs.open('items.bot.ini','r', encoding='utf-8') as config_file:
	for line in config_file:
		if '=' in line:
			zer = u"" + line.replace('"',"")
			zen = zer.split('=')
			zep = zen[1].split(',')
			db_stock[zen[0]] = [float(zep[0]), int(zep[1])]
# FLAGS
admins_ids = [642331433]
groupID = -1002277492706
ru_unicode = "&#127479;&#127482;"
ua_unicode = "&#127482; &#127462;"
en_unicode = "&#58636;"
# FLAGS
bot = Bot(token="7571138296:AAHPfPOw3l5cx85OAaKQeyVifzDgZDASTSg")
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.ERROR)
async def get_rank(player_id, ranks):
    sorted_ranks = sorted(ranks.items(), key=lambda x: x[1], reverse=True)
    for index, (player, score) in enumerate(sorted_ranks, start=1):
        if player == player_id:
            return index
    return None
async def getlang(user):
	return db_users[user.id][1].replace('\n', '')
async def updateUser(user):
	with codecs.open('users.ini','r', encoding='utf-8') as uf:
		users_list = uf.readlines()
		uf.close()
	with codecs.open('users.ini','w', encoding='utf-8') as uf:
		for i in range(len(users_list)):
			line = users_list[i]
			if f"{user.id}" in line: 
				users_list[i] = f"{user.id}=\"{db_users[user.id][0]}\",\"{db_users[user.id][1]}\",\"{db_users[user.id][2]}\",\"{db_users[user.id][3]}\"\n"
		uf.write(''.join(users_list))
		uf.close()
async def open_cabinet(user, message):
	await message.delete()
	lang = await getlang(user)
	welcome_msg = globals()[f"welcome_msg_authed_{lang}"]
	welcome_msg_btn1 = globals()[f"welcome_msg_authed_{lang}_btn1"]
	welcome_msg_btn2 = globals()[f"welcome_msg_authed_{lang}_btn2"]
	welcome_msg_btn3 = globals()[f"welcome_msg_authed_{lang}_btn3"]
	catalog_btn = InlineKeyboardButton(text=welcome_msg_btn1, callback_data="CATALOG")
	account_btn = InlineKeyboardButton(text=welcome_msg_btn2, callback_data="ACCOUNT")
	support_btn = InlineKeyboardButton(text=welcome_msg_btn3, callback_data="SUPPORT")
	keyboard_inline = InlineKeyboardMarkup().add(catalog_btn)
	keyboard_inline.add(account_btn, support_btn)
	await message.answer(f"{welcome_msg}".replace('_name_', user.username), parse_mode=types.ParseMode.HTML, reply_markup=keyboard_inline)
async def open_catalog(lang, message, user):
	welcome_msg = globals()[f"welcome_msg_authed_{lang}_catalog"]
	back_msg = globals()[f"welcome_msg_authed_{lang}_back_btn"]
	soon_msg = globals()[f"welcome_msg_authed_{lang}_soon"]
	keyboard_inline = InlineKeyboardMarkup(row_width=1)
	for country in db_stock:
		cntry = db_countries[country][lang]
		present = 1 if db_users[user.id][3] == 0 else db_users[user.id][3] + 1
		presented = db_users[user.id][2] - present * 50
		if db_stock[country][1] != 0:
			if presented >= 0:
				text = f"{cntry} - 0$ 🎁"
			else:
				text = f"{cntry} - {db_stock[country][0]}$ ✅"
		else:
			text = f"{cntry} - {soon_msg} 🚫"
		cntry_btn = InlineKeyboardButton(text, callback_data=country)
		keyboard_inline.add(cntry_btn)
	back_btn = InlineKeyboardButton(text=back_msg, callback_data="BACK")
	keyboard_inline = keyboard_inline.add(back_btn)
	await message.answer_photo(InputFile("images/photo2.png"), f"{welcome_msg}".replace('_name_', user.username), parse_mode=types.ParseMode.HTML, reply_markup=keyboard_inline)
async def open_account(lang, message, user):
	userData = db_users[user.id]
	welcome_msg = globals()[f"welcome_msg_authed_{lang}_account"]
	pay_msg = globals()[f"welcome_msg_authed_{lang}_pay"]
	welcome_msg_btn1 = globals()[f"welcome_msg_authed_{lang}_back_btn"]
	no_rank_msg = globals()[f"welcome_msg_authed_{lang}_no_rank"]
	back_btn = InlineKeyboardButton(text=welcome_msg_btn1, callback_data="BACK")
	pay_btn = InlineKeyboardButton(text=pay_msg, callback_data="DEPOSIT")
	keyboard_inline = InlineKeyboardMarkup().add(pay_btn).add(back_btn)
	rank =  await get_rank(user.id, ranks)
	if rank == None: rank = no_rank_msg
	else: rank = f"#{rank}"
	present = 1 if db_users[user.id][3] == 0 else db_users[user.id][3] + 1
	left_for_present = db_users[user.id][2] - present * 50
	if left_for_present < 0: left_for_present *= -1
	await message.answer(f"{welcome_msg}".replace('^', '\n').replace('_name_', user.username).replace('+', str(db_users[user.id][3])).replace('~', str(left_for_present)).replace('%', str(userData[0])).replace('*', str(userData[1])).replace('@', str(userData[2])).replace('&', rank), parse_mode=types.ParseMode.HTML, reply_markup=keyboard_inline)
@dp.callback_query_handler(text=["DEPOSIT"]) 
async def check_button(call: types.CallbackQuery, state: FSMContext):
	try:
		await state.finish()
	except:
		pass
	lang = await getlang(call.from_user)
	await call.message.delete()
	welcome_msg = globals()[f"welcome_msg_authed_{lang}_pay_text"]
	welcome_msg_btn0 = globals()[f"welcome_msg_authed_{lang}_back_btn"]
	back_btn = InlineKeyboardButton(text=welcome_msg_btn0, callback_data="BACK")
	keyboard_inline = InlineKeyboardMarkup().add(back_btn)
	await Form.waiting_for_amount.set()
	await call.message.answer(f"{welcome_msg}".replace('_name_', call.from_user.username),  parse_mode=types.ParseMode.HTML, reply_markup=keyboard_inline)
	await call.answer()
@dp.message_handler(state=Form.waiting_for_amount)
async def handle_amount(message: types.Message, state: FSMContext):
    lang = await getlang(message.from_user)
    big_msg = globals()[f"welcome_msg_authed_{lang}_big_payment"].replace('%', "10,000")
    if message.text.isdigit() or float(message.text):
        amount = float(message.text)
        if amount > 10000 or amount < 1:
            await state.reset_state(True)
            await message.answer(f"❌ {big_msg}")
        else:
            welcome_msg_btn1 = globals()[f"welcome_msg_authed_{lang}_back_btn"]
            welcome_msg_authed_check = globals()[f"welcome_msg_authed_{lang}_check"]
            pay_msg = globals()[f"welcome_msg_authed_{lang}_pay"]
            pay_now_msg = globals()[f"welcome_msg_authed_{lang}_pay_now"]
            fiat_invoice = await crypto.create_invoice(amount=amount, fiat='USD', asset=Assets.USDT)
            fiat_invoice.hidden_message = md5(str(message.from_user.id) + ':' + str(fiat_invoice.invoice_id))
            pay_btn = InlineKeyboardButton(text=pay_msg, url=fiat_invoice.bot_invoice_url)
            check_btn = InlineKeyboardButton(text=welcome_msg_authed_check, callback_data="CHECK_PAYMENT")
            back_btn = InlineKeyboardButton(text=welcome_msg_btn1, callback_data="BACK")
            keyboard_inline = InlineKeyboardMarkup().add(pay_btn).add(check_btn).add(back_btn)
            await state.update_data(amount=amount, invoice=fiat_invoice.invoice_id)
            await state.reset_state(False)
            await message.answer(f"{pay_now_msg}".replace('%', str(amount)).replace('^', '\n'), reply_markup=keyboard_inline)
    else:
        pay_correct_msg = globals()[f"welcome_msg_authed_{lang}_pay_correct"]
        await message.answer(f"❌ {pay_correct_msg}")
async def cantbuy(message, lang):
	welcome_msg_authed_cant_buy = globals()[f"welcome_msg_authed_{lang}_cant_buy"]
	pay_msg = globals()[f"welcome_msg_authed_{lang}_pay"]
	welcome_msg_btn0 = globals()[f"welcome_msg_authed_{lang}_back_btn"]
	pay_btn = InlineKeyboardButton(text=pay_msg, callback_data="DEPOSIT")
	back_btn = InlineKeyboardButton(text=welcome_msg_btn0, callback_data="BACK")
	keyboard_inline = InlineKeyboardMarkup().add(pay_btn).add(back_btn)
	await message.answer(f"{welcome_msg_authed_cant_buy}", parse_mode=types.ParseMode.HTML, reply_markup=keyboard_inline)
@dp.message_handler(state=Pay.waiting_for_count)
async def handle_amount(message: types.Message, state: FSMContext):
    stateData = await state.get_data()
    user = message.from_user
    lang = await getlang(user)
    country = stateData.get("country", None)
    if country is None:
        pay_error = globals()[f"welcome_msg_authed_{lang}_pay_error"]
        await message.answer(f"❌ {pay_error}")
    else:
        amount = db_stock[country][0]
        pay_hz_msg = globals()[f"welcome_msg_authed_{lang}_pay_hz"]
        big_msg = globals()[f"welcome_msg_authed_{lang}_big_kyc_payment"].replace('%', "20")
        if message.text.isdigit():
            count = int(message.text)
            if count > 20 or count < 1:
                await state.reset_state(True)
                await message.answer(f"❌ {big_msg}")
            else:
                if amount is None:
                    await message.answer(f"❌ {pay_hz_msg}")
                else:
                    if db_users[user.id][0] >= count * amount:
                        await state.finish()
                        db_users[user.id][0] -= count * amount
                        db_users[user.id][2] += count
                        await updateUser(user)
                        welcome_msg_btn1 = globals()[f"welcome_msg_authed_{lang}_back_btn"]
                        bought_many = globals()[f"welcome_msg_authed_{lang}_bought_many"]
                        back_btn = InlineKeyboardButton(text=welcome_msg_btn1, callback_data="BACK")
                        keyboard_inline = InlineKeyboardMarkup().add(back_btn)
                        orderID = str(randint(1111111, 9999999))
                        amount = str(amount).replace('.0', '')
                        count = str(count).replace('.0', '')
                        await bot.send_message(groupID, f"<b>===NOTIFICATION===</b>\n@{user.username} купил KYC в стране {db_countries[country][lang]} в количестве {count} шт.\nНомер его заказа: {orderID}\nНаш слоняра 🐘", parse_mode=types.ParseMode.HTML)
                        await message.answer(f"{bought_many}".replace('^', '\n').replace('*', db_countries[country][lang]).replace('~', orderID).replace('@', str(count)), reply_markup=keyboard_inline, parse_mode=types.ParseMode.HTML)
                    else:
                        await state.finish()
                        await cantbuy(message, lang)
        else:
            pay_correct_msg = globals()[f"welcome_msg_authed_{lang}_pay_correct"]
            await message.answer(f"❌ {pay_correct_msg}")
@dp.callback_query_handler(text=["CHECK_PAYMENT"]) 
async def check_button(call: types.CallbackQuery, state: FSMContext):
	lang = await getlang(call.from_user)
	pay_success = globals()[f"welcome_msg_authed_{lang}_pay_success"]
	pay_not_success = globals()[f"welcome_msg_authed_{lang}_pay_not_success"]
	pay_hz = globals()[f"welcome_msg_authed_{lang}_pay_hz"]
	invoice_data = await state.get_data()
	await state.finish()
	amount = invoice_data.get('amount', None)
	invoice = invoice_data.get('invoice', None)
	if invoice is None:
		await call.message.answer(f"❌ {pay_hz}")
	else:
		check_invoice = await crypto.get_invoices(asset=Assets.USDT, invoice_ids=invoice)
		if check_invoice.status == 'paid':
			db_users[call.from_user.id][0] += amount
			await updateUser(call.from_user)
			await call.message.answer(f"✅ {pay_success}".replace('%', str(db_users[call.from_user.id][0])))
			await bot.send_message(groupID, f"<b>===NOTIFICATION===</b>\n@{call.from_user.username} пополнил баланс на {amount}$\nНомер его заказа: {check_invoice.invoice_id}\nНаш слоняра 🐘", parse_mode=types.ParseMode.HTML)
		else:
			await call.message.answer(f"❌ {pay_not_success}")
	await call.answer()
async def open_support(lang, message, user):
	welcome_msg = globals()[f"welcome_msg_authed_{lang}_support"]
	welcome_msg_btn0 = globals()[f"welcome_msg_authed_{lang}_back_btn"]
	welcome_msg_btn1 = globals()[f"welcome_msg_authed_{lang}_support_btn1"]
	welcome_msg_btn2 = globals()[f"welcome_msg_authed_{lang}_support_btn2"]
	welcome_msg_btn3 = globals()[f"welcome_msg_authed_{lang}_support_btn3"]
	welcome_msg_btn4 = globals()[f"welcome_msg_authed_{lang}_support_btn4"]
	usage_urls = {
		"en": "https://telegra.ph/Terms-of-service-01-03-2",
		"ru": "https://telegra.ph/Usloviya-obsluzhivaniya-01-03",
		"ua": "https://telegra.ph/Umovi-obslugovuvannya-01-03"
	}
	faq_urls = {
		"en": "https://telegra.ph/CHddddddddddddddFAQ-01-04",
		"ru": "https://telegra.ph/CHastye-voprosyFAQ-01-04",
		"ua": "https://telegra.ph/CHast%D1%96-pitannyaFAQ-01-04"
	}
	back_btn = InlineKeyboardButton(text=welcome_msg_btn0, callback_data="BACK")
	manager_btn = InlineKeyboardButton(text=welcome_msg_btn1, callback_data="MANAGER")
	faq_btn = InlineKeyboardButton(text=welcome_msg_btn2, url=faq_urls[lang])
	partner_btn = InlineKeyboardButton(text=welcome_msg_btn3, url="https://docs.google.com/forms/d/e/1FAIpQLSdGYU3b8t4KqvaVUca7CYD-2RXepaw4CoK759Cr7KE2qINGRQ/viewform?usp=dialog")
	usage_btn = InlineKeyboardButton(text=welcome_msg_btn4, url=usage_urls[lang])
	keyboard_inline = InlineKeyboardMarkup().add(manager_btn).add(faq_btn).add(partner_btn).add(usage_btn).add(back_btn)
	await message.answer(f"{welcome_msg}".replace('_name_', user.username), parse_mode=types.ParseMode.HTML, reply_markup=keyboard_inline)
@dp.message_handler(commands="start")
async def cmd_test1(message: types.Message):
	user = message.from_user
	if user.id not in list(db_users.keys()):
		await message.delete()
		ru_btn = InlineKeyboardButton(text="Русский", callback_data="RU") 
		ua_btn = InlineKeyboardButton(text="Українська", callback_data="UA") 
		en_btn = InlineKeyboardButton(text="English", callback_data="EN") 
		keyboard_inline = InlineKeyboardMarkup().add(ua_btn, ru_btn, en_btn) 
		await message.answer_photo(InputFile("images/photo1.jpg"), f"{welcome_msg_en}".replace('_name_', user['username']), parse_mode=types.ParseMode.HTML, reply_markup=keyboard_inline)
	else:
		await open_cabinet(user, message)
@dp.callback_query_handler(text=list(db_stock.keys())) 
async def check_button(call: types.CallbackQuery, state: FSMContext):
	country = call.data
	user = call.from_user
	lang = await getlang(user)
	try:
		await state.finish()
	except:
		pass
	if db_stock[country][1] > 0:
		await call.message.delete()
		present = 1 if db_users[user.id][3] == 0 else db_users[user.id][3]+1
		presented = presented = db_users[user.id][2] - present * 50
		if presented < 0 and db_users[user.id][0] >= db_stock[country][0]:
			welcome_msg = globals()[f"welcome_msg_authed_{lang}_pay_count"]
			welcome_msg_btn0 = globals()[f"welcome_msg_authed_{lang}_back_btn"]
			back_btn = InlineKeyboardButton(text=welcome_msg_btn0, callback_data="BACK2")
			keyboard_inline = InlineKeyboardMarkup().add(back_btn)
			state = dp.current_state(user=call.from_user.id)
			await Pay.waiting_for_count.set()
			await state.update_data(country=country)
			await call.message.answer(f"{welcome_msg}".replace('_name_', call.from_user.username),  parse_mode=types.ParseMode.HTML, reply_markup=keyboard_inline)
		else:
			if presented >= 0:
				db_users[user.id][3] += 1
				db_users[user.id][2] += 1
				await updateUser(user)
				welcome_msg_authed_bought = globals()[f"welcome_msg_authed_{lang}_bought"]
				welcome_msg_btn0 = globals()[f"welcome_msg_authed_{lang}_back_btn"]
				back_btn = InlineKeyboardButton(text=welcome_msg_btn0, callback_data="BACK")
				keyboard_inline = InlineKeyboardMarkup().add(back_btn)
				orderID = str(randint(1111111, 9999999))
				await bot.send_message(groupID, f"<b>===NOTIFICATION===</b>\n@{user.username} купил KYC в стране {db_countries[call.data][lang]} (подарок)\nНомер его заказа: {orderID}\nНаш слоняра 🐘", parse_mode=types.ParseMode.HTML)
				await call.message.answer(f"{welcome_msg_authed_bought}".replace('^', '\n').replace('*', db_countries[call.data][lang]).replace('~', orderID), parse_mode=types.ParseMode.HTML, reply_markup=keyboard_inline)
			else:
				welcome_msg_authed_cant_buy = globals()[f"welcome_msg_authed_{lang}_cant_buy"]
				pay_msg = globals()[f"welcome_msg_authed_{lang}_pay"]
				welcome_msg_btn0 = globals()[f"welcome_msg_authed_{lang}_back_btn"]
				pay_btn = InlineKeyboardButton(text=pay_msg, callback_data="DEPOSIT")
				back_btn = InlineKeyboardButton(text=welcome_msg_btn0, callback_data="BACK")
				keyboard_inline = InlineKeyboardMarkup().add(pay_btn).add(back_btn)
				await call.message.answer(f"{welcome_msg_authed_cant_buy}", parse_mode=types.ParseMode.HTML, reply_markup=keyboard_inline)
	await call.answer()
@dp.callback_query_handler(text=["RU", "UA", "EN"]) 
async def check_button(call: types.CallbackQuery):
	if call.from_user.id not in db_users:
		db_users[call.from_user.id] = [0, call.data.lower(), 0, 0]
		await open_cabinet(call.from_user, call.message)
		await call.answer()
		ranks[call.from_user.id] = 0
		with codecs.open('users.ini','a', encoding='utf-8') as users_file:
			users_file.write(f"{call.from_user.id}=\"0\",\"{call.data.lower()}\",\"0\",\"0\"\n")
@dp.callback_query_handler(text=["CATALOG", "ACCOUNT", "SUPPORT"]) 
async def check_button(call: types.CallbackQuery):
	lang = await getlang(call.from_user)
	await call.message.delete()
	if call.data == "CATALOG":
		await open_catalog(lang, call.message, call.from_user)
	if call.data == "ACCOUNT":
		await open_account(lang, call.message, call.from_user)
	if call.data == "SUPPORT":
		await open_support(lang, call.message, call.from_user)
	await call.answer()
@dp.callback_query_handler(text=["BACK2"], state=Pay.waiting_for_count) 
async def check_button(call: types.CallbackQuery, state: FSMContext):
	try:
		await state.finish()
	except:
		pass
	await open_cabinet(call.from_user, call.message)
@dp.callback_query_handler(text=["BACK", "MANAGER"]) 
async def check_button(call: types.CallbackQuery, state: FSMContext):
	lang = await getlang(call.from_user)
	if call.data == "BACK":
		try:
			await state.finish()
		except:
			pass
		await open_cabinet(call.from_user, call.message)
	if call.data == "MANAGER":
		await call.message.delete()
		welcome_msg = globals()[f"welcome_msg_authed_{lang}_support_text"]
		welcome_msg_btn0 = globals()[f"welcome_msg_authed_{lang}_back_btn"]
		back_btn = InlineKeyboardButton(text=welcome_msg_btn0, callback_data="SUPPORT")
		keyboard_inline = InlineKeyboardMarkup().add(back_btn)
		await call.message.answer(f"{welcome_msg}".replace('_name_', call.from_user.username),  parse_mode=types.ParseMode.HTML, reply_markup=keyboard_inline)
		await call.answer()
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)